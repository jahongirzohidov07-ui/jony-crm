import os, sys
import json

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
    "task": "TSK",
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
        "ALTER TABLE users ADD COLUMN exit_type VARCHAR",
        "ALTER TABLE users ADD COLUMN exit_reason VARCHAR",
        "ALTER TABLE users ADD COLUMN exit_date DATE",
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
        # Nomzod kartasi - CV, tajriba, sertifikat, baholar.
        "ALTER TABLE candidates ADD COLUMN cv TEXT",
        "ALTER TABLE candidates ADD COLUMN experience_years FLOAT",
        "ALTER TABLE candidates ADD COLUMN workplaces TEXT",
        "ALTER TABLE candidates ADD COLUMN certificates TEXT",
        "ALTER TABLE candidates ADD COLUMN language_level VARCHAR",
        "ALTER TABLE candidates ADD COLUMN expected_salary FLOAT",
        "ALTER TABLE candidates ADD COLUMN trial_score FLOAT",
        "ALTER TABLE candidates ADD COLUMN interview_score FLOAT",
        "ALTER TABLE candidates ADD COLUMN strengths TEXT",
        "ALTER TABLE candidates ADD COLUMN weaknesses TEXT",
        "ALTER TABLE candidates ADD COLUMN reference_note TEXT",
        "ALTER TABLE candidates ADD COLUMN decision VARCHAR DEFAULT 'pending'",
        "UPDATE candidates SET decision = 'pending' WHERE decision IS NULL",
        # Xodim kartasi - rahbar va ishga kirgan sana.
        "ALTER TABLE users ADD COLUMN manager_id INTEGER",
        "ALTER TABLE users ADD COLUMN hired_date DATE",
        "ALTER TABLE users ADD COLUMN phone VARCHAR",
        "ALTER TABLE users ADD COLUMN birth_date DATE",
        "ALTER TABLE users ADD COLUMN position VARCHAR",
        "ALTER TABLE users ADD COLUMN photo TEXT",
        "UPDATE users SET hired_date = DATE(created_at) WHERE hired_date IS NULL",
        # Ustozning maksimal yuklamasi - undan oshsa tizim yo'l qo'ymaydi.
        "ALTER TABLE teachers ADD COLUMN max_groups INTEGER",
        "ALTER TABLE teachers ADD COLUMN max_lessons_per_day INTEGER",
        # O'quvchining hozirgi darajasi - guruhga qo'shishda tekshiriladi.
        "ALTER TABLE students ADD COLUMN subject VARCHAR",
        "ALTER TABLE students ADD COLUMN level VARCHAR",
        # Filial reytingi og'irliklari (JSON) - strategiya o'zgarsa
        # foizlar ham o'zgaradi.
        "ALTER TABLE branches ADD COLUMN rating_weights TEXT",
        # Coin do'koni: sovg'a kategoriyasi va so'rov holati
        "ALTER TABLE rewards ADD COLUMN category VARCHAR",
        "ALTER TABLE reward_redemptions ADD COLUMN status VARCHAR DEFAULT 'given'",
        "ALTER TABLE reward_redemptions ADD COLUMN requested_by_student INTEGER DEFAULT 0",
        "ALTER TABLE reward_redemptions ADD COLUMN given_by VARCHAR",
        "ALTER TABLE reward_redemptions ADD COLUMN given_at TIMESTAMP",
        "ALTER TABLE reward_redemptions ADD COLUMN note VARCHAR",
        # Eski yozuvlar allaqachon berilgan sovg'alar
        "UPDATE reward_redemptions SET status = 'given' WHERE status IS NULL",
        # O'quvchini o'z hisobiga bog'lash
        "ALTER TABLE students ADD COLUMN user_id INTEGER",
        # "Administrator" endi alohida rol: sotuv menejeri sotuv bilan,
        # administrator qabul va kassa bilan shug'ullanadi. Eskisi
        # sotuv menejeri bo'lib qoladi - hech kim huquqini yo'qotmaydi.
        "ALTER TABLE users ADD COLUMN photo TEXT",
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
        # Ustoz darajasi va karyera xaritasi.
        "ALTER TABLE teachers ADD COLUMN grade VARCHAR",
        "ALTER TABLE teachers ADD COLUMN grade_since DATE",
        "ALTER TABLE teachers ADD COLUMN cert VARCHAR",
        "ALTER TABLE teachers ADD COLUMN cert_score FLOAT",
        "ALTER TABLE teachers ADD COLUMN qualification VARCHAR",
        "ALTER TABLE teachers ADD COLUMN birth_date DATE",
        "ALTER TABLE teachers ADD COLUMN skill_score FLOAT",
        "ALTER TABLE teachers ADD COLUMN support_months FLOAT",
        "ALTER TABLE teachers ADD COLUMN remediation_until DATE",
        "ALTER TABLE teachers ADD COLUMN remediation_reason VARCHAR",
        # Guruh stavkasi qo'lda kiritilganmi (daraja o'zgarganda
        # tegilmasligi uchun). NULL qolganini keyingi blok to'ldiradi.
        "ALTER TABLE groups ADD COLUMN rate_manual INTEGER",
        # Daraja jadvaliga keyin qo'shilgan ustunlar.
        "ALTER TABLE teacher_grades ADD COLUMN needs_qualification INTEGER DEFAULT 0",
        "ALTER TABLE teacher_grades ADD COLUMN min_results INTEGER",
        "ALTER TABLE teacher_grades ADD COLUMN result_band FLOAT",
        "ALTER TABLE teacher_grades ADD COLUMN min_age INTEGER",
        "ALTER TABLE teacher_grades ADD COLUMN min_skill FLOAT",
        "ALTER TABLE teacher_grades ADD COLUMN level_pass_percent FLOAT DEFAULT 60",
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

            # Coin do'koni: plakatdagi sovg'alar bazaga tushadi.
            # HAR BIR sovg'a alohida tekshiriladi - jadval bo'sh
            # bo'lmasa ham yetishmayotgani qo'shiladi. Mavjud
            # sovg'aning NARXIGA tegilmaydi: asoschi uni o'zgartirgan
            # bo'lishi mumkin.
            have = {(r.name or "").strip().lower()
                    for r in db.query(models.Reward).all()}
            added = False
            for name, cost, cat in roles.DEFAULT_REWARDS:
                if name.strip().lower() in have:
                    continue
                db.add(models.Reward(name=name, cost=cost,
                                     category=cat, active=1))
                added = True
            if added:
                db.commit()

            # Kategoriyasi yo'q sovg'alarga ro'yxatdan topib qo'yamiz -
            # do'konda guruhlanib chiqsin.
            by_name = {n.strip().lower(): c for n, _, c in roles.DEFAULT_REWARDS}
            changed = False
            for r in db.query(models.Reward).filter(
                    models.Reward.category.is_(None)).all():
                r.category = by_name.get((r.name or "").strip().lower(),
                                         "special")
                changed = True
            if changed:
                db.commit()

            # Ustoz darajalari jadvali. Hujjatdagi raqamlar bir marta
            # tushadi; asoschi keyin o'zgartirsa - qayta yozilmaydi.
            # Hujjatning o'zida ham "talablar o'zgarib turishi mumkin"
            # deb yozilgan, shuning uchun manba - baza, kod emas.
            have_g = {g.key for g in db.query(models.TeacherGrade).all()}
            added = False
            for i, row in enumerate(roles.TEACHER_GRADES):
                (key, label, rate, months, mn, mx, cert_lbl, cert_min,
                 promote, demote, demote_to) = row
                if key in have_g:
                    continue
                db.add(models.TeacherGrade(
                    key=key, label=label, order_no=i,
                    rate_per_student=rate, min_months=months,
                    min_groups=mn, max_groups=mx,
                    cert_label=cert_lbl, cert_min=cert_min,
                    promote_pass_rate=promote,
                    demote_below=demote, demote_to=demote_to,
                    needs_qualification=1 if key in
                    roles.QUALIFICATION_REQUIRED_FOR else 0,
                    min_results=(roles.HEAD_MIN_RESULTS if key == "head"
                                 else roles.METODIST_MIN_RESULTS
                                 if key == "metodist" else None),
                    result_band=(roles.HEAD_RESULT_BAND if key == "head"
                                 else roles.METODIST_RESULT_BAND
                                 if key == "metodist" else None),
                    min_age=(roles.HEAD_MIN_AGE if key in ("head", "metodist")
                             else roles.TEACHER_MIN_AGE),
                    min_skill=(roles.HEAD_MIN_SKILL if key in ("head", "metodist")
                               else roles.TEACHER_MIN_SKILL),
                    level_pass_percent=roles.LEVEL_PASS_PERCENT,
                    active=1))
                added = True
            if added:
                db.commit()

            # Darajasi belgilanmagan ustozlar birinchi darajada
            # boshlanadi - stavkasi bo'sh qolib ketmasin.
            changed = False
            for t in db.query(models.Teacher).filter(
                    models.Teacher.grade.is_(None)).all():
                t.grade = roles.FIRST_GRADE
                t.grade_since = t.hired_date or date.today()
                changed = True
            if changed:
                db.commit()

            # Eski guruhlarda stavka qo'lda kiritilgan bo'lishi mumkin.
            # Darajaning narxiga to'g'ri kelmasa - "qo'lda" deb
            # belgilaymiz, aks holda birinchi avtomat yangilanish
            # kiritilgan narxni o'chirib yuborardi.
            rates = {g.key: g.rate_per_student
                     for g in db.query(models.TeacherGrade).all()}
            teachers = {t.id: t for t in db.query(models.Teacher).all()}
            changed = False
            for g in db.query(models.Group).filter(
                    models.Group.rate_manual.is_(None)).all():
                t = teachers.get(g.teacher_id)
                want = rates.get(t.grade if t else None)
                cur = g.teacher_rate_per_student or 0
                g.rate_manual = 1 if (cur and want and cur != want) else 0
                changed = True
            if changed:
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
    "task": "TSK",
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


def can_see_all_branches(user: models.User) -> bool:
    """Butun tashkilotni ko'radimi yoki bitta filialgami."""
    return user.role in tuple(roles.ORG_WIDE_ROLES) or not user.branch_id


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


# =====================================================================
#  SMM AVTOMAT VAZIFALARI
#  SMM eslab qolishi shart emas: yangi xodim kelsa yoki o'quvchi
#  natija qilsa — vazifa o'zi paydo bo'ladi, hamma ma'lumoti bilan.
# =====================================================================
def _smm_user(db: Session, branch_id: int | None = None) -> models.User | None:
    """Vazifa kimga tushadi. SMM manager bo'lmasa - asoschiga."""
    q = db.query(models.User).filter(models.User.role == roles.SMM_MANAGER,
                                     models.User.is_active == 1)
    if branch_id:
        row = q.filter(models.User.branch_id == branch_id).first()
        if row:
            return row
    return q.first() or (db.query(models.User)
                         .filter(models.User.role == roles.FOUNDER,
                                 models.User.is_active == 1).first())


def _make_smm_task(db: Session, *, kind: str, title: str, description: str,
                   branch_id: int | None = None,
                   priority: str = "normal") -> models.Task | None:
    """SMM uchun vazifa yaratadi. Xuddi shunday ochiq vazifa bo'lsa
    takror yaratilmaydi — ro'yxat bir xil vazifalar bilan to'lib
    ketmasligi kerak."""
    exists = (db.query(models.Task)
              .filter(models.Task.title == title,
                      ~models.Task.status.in_(roles.TASK_CLOSED)).first())
    if exists:
        return exists
    assignee = _smm_user(db, branch_id)
    t = models.Task(
        title=title,
        description=description,
        assignee_id=assignee.id if assignee else None,
        branch_id=branch_id,
        deadline=date.today() + timedelta(
            days=roles.SMM_TASK_DEADLINE_DAYS.get(kind, 7)),
        priority=priority,
        source="manual",
        created_by="Tizim",
    )
    db.add(t)
    db.flush()
    _ensure_public_id(db, "task", t)
    return t


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


def _smm_achievement_task(db: Session, s: models.Student, *,
                          what: str, detail: str = "") -> None:
    """O'quvchi natija qildi — video olish kerak. Vazifa ichida
    SMM'ga kerak bo'ladigan hamma narsa turadi: qachon kelgan, qanday
    daraja bilan kelgan, qancha o'qigan."""
    today = date.today()
    joined = s.enrolled_date
    months = (round((today - joined).days / 30.4, 1) if joined else None)

    # Kelganidagi darajasi: birinchi guruhining darajasi
    first_level = None
    log = (db.query(models.AuditLog)
           .filter(models.AuditLog.entity == "student",
                   models.AuditLog.entity_id == s.id,
                   models.AuditLog.action.in_(["group_move", "create"]))
           .order_by(models.AuditLog.created_at).first())
    if log and log.new_value:
        g = (db.query(models.Group)
             .filter(models.Group.name == log.new_value).first())
        if g:
            first_level = roles.LEVEL_LABELS.get(g.level or "", g.level)
    now_level = roles.LEVEL_LABELS.get(s.level or "", s.level)

    _make_smm_task(
        db, kind="achievement",
        title=f"Natija: {s.full_name} — {what}",
        description=(
            f"Nima qildi: {what}\n"
            + (f"{detail}\n" if detail else "")
            + f"Qachon kelgan: {joined.isoformat() if joined else '—'}\n"
            f"Kelganidagi darajasi: {first_level or '—'}\n"
            f"Hozirgi darajasi: {now_level or '—'}\n"
            f"Qancha o'qidi: {months if months is not None else '—'} oy\n"
            f"Guruhi: {s.group.name if s.group else '—'}\n"
            f"Ustozi: {s.group.teacher.full_name if s.group and s.group.teacher else '—'}\n"
            f"Telefon: {s.phone or s.parent_phone or '—'}\n\n"
            "Kerak: o'quvchi bilan qisqa video — nima o'zgardi, "
            "qanday his qilyapti, kimga tavsiya qiladi."),
        branch_id=s.branch_id,
        priority="high")


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
    # AVTOMAT: SMM'ga yangi xodimni suratga olish vazifasi
    _smm_new_staff_task(db, new_user)
    db.commit()
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
        was = target.is_active
        target.is_active = int(payload.is_active)
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
        target.password_hash = hash_password(payload.password)
    # Fiks oylik - KPI hisobining asosi, shuning uchun uni faqat asoschi
    # (roles.USER_ADMIN) o'zgartira oladi; endpoint allaqachon shu bilan
    # himoyalangan. exclude_unset orqali "berilmagan" va "0 qilindi"
    # holatlarini ajratamiz.
    given = payload.model_dump(exclude_unset=True)
    if "fix_salary" in given:
        target.fix_salary = payload.fix_salary

    # Xodim kartasi maydonlari. exclude_unset — "berilmagan" va
    # "bo'shatildi" holatlarini ajratadi, aks holda tahrirlash oynasida
    # tegilmagan maydon ham tozalanib ketardi.
    for f in ("phone", "birth_date", "position", "manager_id",
              "hired_date", "photo"):
        if f in given:
            setattr(target, f, given[f])

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

    # AVTOMAT XP: kelgani uchun ball va davomat ketma-ketligi.
    # Ustoz hech narsa bosmaydi.
    try:
        _xp_for_attendance(db, lesson, by_user=user)
    except Exception:
        db.rollback()

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

    # AVTOMAT XP: natija bandi, o'sish bonusi, unit/imtihon va mock.
    # Bitta natijaga faqat bitta band qoidasi ishlaydi.
    try:
        _xp_for_exam(db, exam, by_user=user)
    except Exception:
        db.rollback()

    # AVTOMAT: yuqori natija - SMM'ga video olish vazifasi.
    # Ustoz alohida hech kimga aytishi shart emas.
    for r in exam.results:
        if r.absent or r.percent is None:
            continue
        if r.percent < roles.CERTIFICATE_RECOMMEND_PERCENT:
            continue
        st = db.query(models.Student).get(r.student_id)
        if not st:
            continue
        _smm_achievement_task(
            db, st,
            what=f"{roles.EXAM_KIND_LABELS.get(exam.kind, exam.kind)} "
                 f"{r.percent}%",
            detail=(f"Band: {r.band}" if r.band is not None
                    else f"Ball: {r.score}/{exam.max_score}"))
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
    """Ustozlar ish haqi - YOQLAMADAN avtomat hisoblanadi.

    Uni Xarajatlar bo'limiga qo'lda kiritish shart emas (va kiritilmasligi
    ham kerak - aks holda ikki marta hisoblanadi). Hech qayerda
    saqlanmaydi ham: har safar darslardan qayta hisoblanadi, shuning
    uchun yoqlama tuzatilsa oylik ham o'zi to'g'rilanadi."""
    try:
        y, m = int(period[:4]), int(period[5:7])
    except (ValueError, IndexError):
        return 0.0
    start, end = billing.month_bounds(y, m)

    gq = db.query(models.Group)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        gq = gq.filter(models.Group.branch_id == user.branch_id)
    elif branch_id:
        gq = gq.filter(models.Group.branch_id == branch_id)
    groups = {g.id: g for g in gq.all()}
    if not groups:
        return 0.0

    lessons = (db.query(models.Lesson)
               .filter(models.Lesson.group_id.in_(list(groups)),
                       models.Lesson.held == 1,
                       models.Lesson.date >= start,
                       models.Lesson.date <= end).all())
    total = 0.0
    rates = billing.grade_rates(db)
    for l in lessons:
        g = groups.get(l.group_id)
        if not g or l.teacher_id is None:
            continue
        rate, _ = billing.lesson_rate(db, g, l, rates)
        total += billing.lesson_student_count(db, l) * rate
    return round(total, 2)


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
                              roles.TEACHER, roles.SUPPORT_TEACHER)),
):
    """Bir oylik ustozlar ish haqi.

    Manba - YOQLAMA. Hech qanday "hisoblash" tugmasi yo'q: ro'yxat
    har safar darslardan qayta hisoblanadi. Yoqlama tuzatilsa oylik
    ham o'zi to'g'rilanadi.

    "paid" - ustozga haqiqatda berilgan pul (avans + oylik)."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)

    tq = scope_to_branch(db.query(models.Teacher), models.Teacher,
                         user, branch_id)

    # O'qituvchi faqat O'ZINING oyligini ko'radi - hamkasbining maoshi
    # unga ko'rinmaydi.
    own_only = user.role not in tuple(roles.FINANCE_ACCESS
                                      + roles.SALARY_VIEW_ALL)
    if own_only:
        me = _teacher_of_user(db, user)
        if not me:
            return {"period": period, "rows": [], "teacher_count": 0,
                    "total": 0.0, "paid": 0.0, "unpaid": 0.0,
                    "own_only": True}
        tq = tq.filter(models.Teacher.id == me.id)

    rows = []
    for t in tq.all():
        e = _teacher_earned(db, t.id, since=start, until=end)
        if e["amount"] == 0:
            continue
        paid = _teacher_paid(db, t.id, since=start, until=end)
        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "groups": [{
                "group_id": g["group_id"],
                "group": g["group"],
                "students": (round(g["attendances"] / g["lessons"])
                             if g["lessons"] else 0),
                "held_lessons": g["lessons"],
                "taught_lessons": g["lessons"],
                "attendances": g["attendances"],
                "rate": g["rate"],
                "rate_per_student_month": g["rate_per_student_month"],
                "standard_lessons": g["standard_lessons"],
                "amount": round(g["amount"], 2),
            } for g in e["by_group"]],
            "students": sum(round(g["attendances"] / g["lessons"])
                            for g in e["by_group"] if g["lessons"]),
            "lessons": e["lessons"],
            "attendances": e["attendances"],
            "amount": e["amount"],
            "paid_amount": paid,
            "left": round(e["amount"] - paid, 2),
        })

    rows.sort(key=lambda r: -r["amount"])
    total = round(sum(r["amount"] for r in rows), 2)
    paid = round(sum(r["paid_amount"] for r in rows), 2)
    return {
        "period": period,
        "rows": rows,
        "total": total,
        "paid": paid,
        "unpaid": round(total - paid, 2),
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

        # Sotuv menejeri va administrator FAQAT o'zining KPI'sini
        # ko'radi - hamkasbining bonusi unga ko'rinmaydi.
        if (user.role not in tuple(roles.FULL_ACCESS + [roles.FINANCE_DIRECTOR])
                and a.id != user.id):
            continue
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
    if dimension not in ("branch", "teacher", "group", "subject"):
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
        elif dimension == "subject":
            g = groups.get(s.group_id)
            key = g.subject if g else None
            label = (roles.SUBJECT_LABELS.get(key or "", None)
                     or "Fan belgilanmagan")
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
    # Daraja tanlanmagan bo'lsa - birinchisidan boshlaydi. Stavkasi
    # shu darajadan chiqadi, ya'ni guruh ochishda hech narsa
    # kiritilmasa ham to'g'ri hisoblanadi.
    teacher.grade = teacher.grade or roles.FIRST_GRADE
    teacher.grade_since = teacher.hired_date or date.today()
    _sync_teacher_left_date(teacher)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    db.add(models.TeacherGradeEvent(
        teacher_id=teacher.id, from_grade=None, to_grade=teacher.grade,
        kind="set", effective_from=teacher.grade_since,
        reason="Ishga qabul qilindi", decided_by=user.full_name))
    db.commit()
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
    given = payload.model_dump(exclude_unset=True)
    new_grade = given.pop("grade", None)
    for k, v in given.items():
        setattr(teacher, k, v)
    _sync_teacher_left_date(teacher)

    # Daraja o'zgarsa - tarixga yoziladi va guruh stavkalari yangilanadi.
    if new_grade and new_grade != teacher.grade:
        if new_grade not in _grade_map(db):
            raise HTTPException(400, "Bunday daraja yo'q")
        _set_grade(db, teacher, new_grade, kind="set",
                   reason="Qo'lda o'zgartirildi", by=user.full_name)
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


# =====================================================================
#  Avtomatik tekshiruvlar
#  Xatoni odam qilmaydi - tizim yo'l qo'ymaydi. Har bir tekshiruv
#  {"key", "label", "severity", "message"} qaytaradi. severity="block"
#  bo'lsa saqlashga ruxsat berilmaydi.
# =====================================================================
def _problem(key: str, message: str) -> dict:
    return {
        "key": key,
        "label": roles.CHECK_LABELS.get(key, key),
        "severity": roles.CHECK_SEVERITY.get(key, "warn"),
        "message": message,
    }


def _group_slot(g) -> tuple:
    """Guruhning dars vaqti: ("09:00", "11:00"). Bo'lmasa (None, None)."""
    t = (getattr(g, "lesson_time", None) or "").strip()
    if not t:
        return None, None
    parts = [x.strip() for x in t.replace("—", "-").split("-")]
    if len(parts) == 2 and roles.time_to_minutes(parts[0]) is not None:
        return parts[0], parts[1]
    if roles.time_to_minutes(t) is not None:
        return t, roles.lesson_end_time(t)
    return None, None


def _group_days(g) -> list:
    return [d for d in (getattr(g, "lesson_days", None) or "").split(",") if d]


def _check_teacher_load(db: Session, teacher_id: int,
                        group_id: int | None) -> list:
    """Ustoz nechta guruh olib bora oladi va hozir yangi guruh olishi
    mumkinmi. Dars jadvaliga bog'liq emas — shuning uchun alohida."""
    problems = []
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        return problems

    # Chegara DARAJADAN chiqadi: Junior 1 ta, Middle 2-3 ta,
    # Senior 4-5 ta, Expert 6-7 ta. Ustozga alohida chegara
    # qo'yilgan bo'lsa - o'sha ustun.
    grade_max = None
    if t.grade:
        gr = db.query(models.TeacherGrade).filter(
            models.TeacherGrade.key == t.grade).first()
        grade_max = gr.max_groups if gr else None
    max_groups = (t.max_groups or grade_max or roles.TEACHER_MAX_GROUPS)

    # Natijasi 50% dan past chiqqan ustozga muddat tugagunicha YANGI
    # guruh ochilmaydi — hujjatdagi qoida shunday.
    if (t.remediation_until and t.remediation_until >= date.today()
            and not group_id):
        problems.append(_problem(
            "teacher_overload",
            f"{t.full_name} qayta tayyorlash bosqichida — "
            f"{t.remediation_until.isoformat()} gacha yangi guruh "
            f"ochilmaydi. Sabab: {t.remediation_reason or '—'}"))

    total = db.query(models.Group).filter(
        models.Group.teacher_id == teacher_id)
    if group_id:
        total = total.filter(models.Group.id != group_id)
    n_groups = total.count() + 1
    if n_groups > max_groups:
        gl = roles.GRADE_LABELS.get(t.grade or "")
        problems.append(_problem(
            "teacher_overload",
            f"Ustozda {n_groups} ta guruh bo'ladi — chegara "
            f"{max_groups} ta"
            + (f" ({gl} darajasi uchun)." if gl and grade_max
               and max_groups == grade_max else ".")))
    return problems


def _check_schedule(db: Session, *, group_id, teacher_id, room_id,
                    lesson_days, lesson_time, branch_id=None) -> list:
    """Jadval to'qnashuvlarini topadi. group_id berilsa o'sha guruhning
    o'zi hisobga olinmaydi (o'zini o'ziga to'qnash deb ko'rsatmaslik uchun)."""
    problems = []
    days = [d for d in (lesson_days or "").split(",") if d]
    start, end = _group_slot(type("T", (), {"lesson_time": lesson_time})())

    # Guruh soni va qayta tayyorlash - dars jadvaliga bog'liq emas.
    # Vaqt kiritilmagan bo'lsa ham tekshiriladi, aks holda jadvalsiz
    # guruh ochib chegaradan chiqib ketish mumkin bo'lardi.
    if teacher_id:
        problems += _check_teacher_load(db, teacher_id, group_id)

    if not days or not start:
        return problems

    others = db.query(models.Group).all()
    day_counts = {}
    teacher_slots = []

    for o in others:
        if group_id and o.id == group_id:
            continue
        o_days = _group_days(o)
        o_start, o_end = _group_slot(o)
        if not o_days or not o_start:
            continue
        shared = [d for d in days if d in o_days]
        if not shared:
            continue
        clash = roles.ranges_overlap(start, end, o_start, o_end)

        if teacher_id and o.teacher_id == teacher_id:
            for d in shared:
                day_counts[d] = day_counts.get(d, 0) + 1
                teacher_slots.append((d, o_start, o_end, o.name))
            if clash:
                problems.append(_problem(
                    "teacher_clash",
                    f"Ustoz shu vaqtda \"{o.name}\" guruhida dars beradi "
                    f"({roles.WEEKDAY_LABELS.get(shared[0], shared[0])} "
                    f"{o_start}-{o_end})."))
        if room_id and o.room_id == room_id and clash:
            room = db.query(models.Room).get(room_id)
            problems.append(_problem(
                "room_clash",
                f"\"{room.name if room else 'Xona'}\" xonasi shu vaqtda "
                f"\"{o.name}\" guruhi tomonidan band."))

    # Ustozning kunlik yuklamasi (jadvalga bog'liq)
    if teacher_id:
        t = db.query(models.Teacher).get(teacher_id)
        max_day = (t.max_lessons_per_day if t and t.max_lessons_per_day
                   else roles.TEACHER_MAX_LESSONS_PER_DAY)
        for d in days:
            n = day_counts.get(d, 0) + 1
            if n > max_day:
                problems.append(_problem(
                    "teacher_overload",
                    f"{roles.WEEKDAY_LABELS.get(d, d)} kuni ustozda {n} ta "
                    f"dars bo'ladi — chegara {max_day} ta."))
                break

        # Darslar orasidagi bo'shliq
        for d in days:
            slots = sorted(
                [(roles.time_to_minutes(a), roles.time_to_minutes(b))
                 for dd, a, b, _ in teacher_slots if dd == d]
                + [(roles.time_to_minutes(start), roles.time_to_minutes(end))]
            )
            for i in range(len(slots) - 1):
                gap = (slots[i + 1][0] - slots[i][1]) / 60
                if gap > roles.MAX_GAP_HOURS:
                    problems.append(_problem(
                        "bad_gap",
                        f"{roles.WEEKDAY_LABELS.get(d, d)} kuni ustozning "
                        f"darslari orasida {gap:.0f} soat bo'shliq qoladi."))
                    break
            else:
                continue
            break

    # Xona sig'imi guruh o'quvchilaridan kichik bo'lmasin
    if room_id and group_id:
        room = db.query(models.Room).get(room_id)
        n = db.query(models.Student).filter(
            models.Student.group_id == group_id,
            models.Student.status != "archived").count()
        if room and room.capacity and n > room.capacity:
            problems.append(_problem(
                "over_capacity",
                f"Guruhda {n} ta o'quvchi bor, \"{room.name}\" xonasi esa "
                f"{room.capacity} kishilik."))
    return problems


def _check_enrolment(db: Session, s: models.Student, g: models.Group) -> list:
    """O'quvchini guruhga qo'shishdan oldingi tekshiruvlar."""
    problems = []
    if not g:
        return problems

    n = db.query(models.Student).filter(
        models.Student.group_id == g.id,
        models.Student.status != "archived",
        models.Student.id != s.id).count()
    rooms = {r.id: r for r in db.query(models.Room).all()}
    cap = _group_capacity(g, rooms)
    if cap and n + 1 > cap:
        problems.append(_problem(
            "over_capacity",
            f"\"{g.name}\" guruhida {n} ta o'quvchi bor, sig'im {cap} ta. "
            f"Yana bittasi sig'maydi."))

    # Daraja mosligi. O'quvchining darajasi hali yo'q bo'lsa - bu birinchi
    # guruhi, tekshiradigan narsa yo'q.
    if s.level and g.level and s.level != g.level:
        problems.append(_problem(
            "level_mismatch",
            f"O'quvchining darajasi "
            f"\"{roles.LEVEL_LABELS.get(s.level, s.level)}\", guruh esa "
            f"\"{roles.LEVEL_LABELS.get(g.level, g.level)}\"."))
    elif s.subject and g.subject and s.subject != g.subject:
        problems.append(_problem(
            "level_mismatch",
            f"O'quvchi \"{roles.SUBJECT_LABELS.get(s.subject, s.subject)}\" "
            f"o'qiydi, guruh esa "
            f"\"{roles.SUBJECT_LABELS.get(g.subject, g.subject)}\" guruhi."))
    return problems


def _raise_if_blocked(problems: list, *, force: bool = False):
    """severity="block" bo'lgan muammo bo'lsa saqlashni to'xtatadi.
    force=True bo'lsa faqat ogohlantirish qoladi - lekin block'ni
    hech kim aylanib o'tolmaydi."""
    blocking = [p for p in problems if p["severity"] == "block"]
    if blocking:
        raise HTTPException(400, {
            "message": blocking[0]["message"],
            "problems": problems,
        })
    if problems and not force:
        raise HTTPException(409, {
            "message": problems[0]["message"],
            "problems": problems,
            "can_force": True,
        })


@app.post("/api/checks/schedule")
def check_schedule(
    payload: schemas.ScheduleCheck,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Saqlashdan oldin tekshirish - foydalanuvchi xatoni saqlashdan
    oldin ko'radi."""
    problems = _check_schedule(
        db, group_id=payload.group_id, teacher_id=payload.teacher_id,
        room_id=payload.room_id, lesson_days=payload.lesson_days,
        lesson_time=payload.lesson_time)
    return {
        "problems": problems,
        "ok": not problems,
        "blocking": any(p["severity"] == "block" for p in problems),
    }


@app.post("/api/checks/enrolment")
def check_enrolment(
    payload: schemas.EnrolmentCheck,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(payload.student_id)
    g = db.query(models.Group).get(payload.group_id)
    if not s or not g:
        raise HTTPException(404, "Topilmadi")
    problems = _check_enrolment(db, s, g)
    return {
        "problems": problems,
        "ok": not problems,
        "blocking": any(p["severity"] == "block" for p in problems),
    }


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
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    _validate_group_fields(payload)
    data = payload.model_dump()
    _raise_if_blocked(
        _check_schedule(db, group_id=None,
                        teacher_id=data.get("teacher_id"),
                        room_id=data.get("room_id"),
                        lesson_days=data.get("lesson_days"),
                        lesson_time=data.get("lesson_time")),
        force=force)
    group = models.Group(**data)
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
    force: bool = False,
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

    # Ustoz, xona yoki vaqt o'zgarayotgan bo'lsa - to'qnashuvni
    # saqlashdan OLDIN tekshiramiz.
    if any(k in fields for k in
           ("teacher_id", "room_id", "lesson_days", "lesson_time")):
        _raise_if_blocked(
            _check_schedule(
                db, group_id=group.id,
                teacher_id=fields.get("teacher_id", group.teacher_id),
                room_id=fields.get("room_id", group.room_id),
                lesson_days=fields.get("lesson_days", group.lesson_days),
                lesson_time=fields.get("lesson_time", group.lesson_time)),
            force=force)

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
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    changes = payload.model_dump(exclude_unset=True)

    # Yangi guruhga o'tkazilyaptimi - sig'im va daraja tekshiriladi.
    new_gid = changes.get("group_id")
    if new_gid and new_gid != s.group_id:
        g = db.query(models.Group).get(new_gid)
        _raise_if_blocked(_check_enrolment(db, s, g), force=force)
        # O'quvchining darajasi hali yo'q bo'lsa - guruhnikidan olamiz.
        if g and not s.level:
            changes.setdefault("subject", g.subject)
            changes.setdefault("level", g.level)
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
    user=Depends(require_role(*roles.CASH_ACCESS)),
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

    # AVTOMAT: bu o'quvchini kimdir olib kelgan bo'lsa, o'sha odamning
    # referral chegirmasi shu to'lov bilan yoqiladi.
    if payload.kind == "payment":
        if _activate_referrals(db, student_id):
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
        "decision": c.decision or "pending",
        "trial_score": c.trial_score,
        "interview_score": c.interview_score,
        "expected_salary": c.expected_salary,
        "language_level": c.language_level,
        "experience_years": c.experience_years,
    } for c in q.order_by(models.Candidate.created_at.desc()).all()]


@app.get("/api/candidates/{cid}")
def get_candidate(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    """Nomzod kartasi - qaror qabul qilish uchun kerak bo'lgan hammasi
    bir ekranda: CV, tajriba, ballar, kuchli va zaif tomonlari."""
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")

    files = (db.query(models.Attachment)
             .filter(models.Attachment.entity == "candidate",
                     models.Attachment.entity_id == cid)
             .order_by(models.Attachment.created_at.desc()).all())

    # Umumiy ball: probniy dars va intervyu o'rtachasi. Ikkalasi ham
    # bo'lmasa - hali baholanmagan.
    scores = [x for x in (c.trial_score, c.interview_score) if x is not None]
    overall = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "id": c.id,
        "full_name": c.full_name,
        "phone": c.phone,
        "vacancy_id": c.vacancy_id,
        "vacancy": c.vacancy.title if c.vacancy else None,
        "stage": c.stage,
        "stage_label": dict(roles.CANDIDATE_STAGES).get(c.stage, c.stage)
                       if hasattr(roles, "CANDIDATE_STAGES") else c.stage,
        "source": c.source,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "note": c.note,
        "reject_reason": c.reject_reason,
        "hired_date": c.hired_date.isoformat() if c.hired_date else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        # ---- Karta ----
        "cv": c.cv,
        "experience_years": c.experience_years,
        "workplaces": c.workplaces,
        "certificates": c.certificates,
        "language_level": c.language_level,
        "language_level_label": roles.LANGUAGE_LEVEL_LABELS.get(
            c.language_level or "", None),
        "expected_salary": c.expected_salary,
        "trial_score": c.trial_score,
        "interview_score": c.interview_score,
        "overall_score": overall,
        "strengths": c.strengths,
        "weaknesses": c.weaknesses,
        "reference_note": c.reference_note,
        "decision": c.decision or "pending",
        "decision_label": roles.HIRE_DECISION_LABELS.get(
            c.decision or "pending", "—"),
        "files": [{"id": a.id, "name": a.filename, "kind": a.kind,
                   "size": a.size,
                   "created_at": a.created_at.isoformat() if a.created_at else None}
                  for a in files],
        "language_levels": [{"key": k, "label": lbl}
                            for k, lbl in roles.LANGUAGE_LEVELS],
        "decisions": [{"key": k, "label": lbl}
                      for k, lbl in roles.HIRE_DECISIONS],
    }


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


# =====================================================================
#  Onboarding
#  Yangi xodim "ishga tushdi" degani - checklist yopilgani. Aks holda
#  u bir oy davomida "kim menga aytadi" deb yuradi.
# =====================================================================
def _onboarding_rows(db: Session, user_id: int) -> list:
    have = {r.step: r for r in db.query(models.OnboardingStep)
            .filter(models.OnboardingStep.user_id == user_id).all()}
    out = []
    for key, label in roles.ONBOARDING_STEPS:
        r = have.get(key)
        out.append({
            "step": key,
            "label": label,
            "done": bool(r and r.done),
            "done_at": r.done_at.isoformat() if r and r.done_at else None,
            "done_by": r.done_by if r else None,
            "note": r.note if r else None,
        })
    return out


@app.get("/api/staff/{user_id}/onboarding")
def get_onboarding(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    rows = _onboarding_rows(db, user_id)
    done = sum(1 for r in rows if r["done"])
    return {
        "user_id": user_id,
        "full_name": emp.full_name,
        "rows": rows,
        "done": done,
        "total": len(rows),
        "percent": round(done / len(rows) * 100) if rows else 0,
        "complete": done == len(rows),
    }


@app.post("/api/staff/{user_id}/onboarding")
def set_onboarding(
    user_id: int,
    payload: schemas.OnboardingUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.step not in roles.ONBOARDING_KEYS:
        raise HTTPException(400, "Noto'g'ri qadam")
    row = (db.query(models.OnboardingStep)
           .filter(models.OnboardingStep.user_id == user_id,
                   models.OnboardingStep.step == payload.step).first())
    if not row:
        row = models.OnboardingStep(user_id=user_id, step=payload.step)
        db.add(row)
    row.done = 1 if payload.done else 0
    row.done_at = datetime.utcnow() if payload.done else None
    row.done_by = user.full_name if payload.done else None
    if payload.note is not None:
        row.note = payload.note
    db.commit()
    return get_onboarding(user_id, db, user)


# =====================================================================
#  Xodim kartasi
#  Bir odam haqidagi hamma narsa bitta ekranda. Rahbar qaror qabul
#  qilishdan oldin uch joyga kirib chiqmasligi kerak.
# =====================================================================
@app.get("/api/staff/{user_id}/events")
def staff_events(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    rows = (db.query(models.StaffEvent)
            .filter(models.StaffEvent.user_id == user_id)
            .order_by(models.StaffEvent.happened_on.desc()).all())
    return {
        "rows": [{
            "id": e.id, "kind": e.kind,
            "kind_label": roles.STAFF_EVENT_LABELS.get(e.kind, e.kind),
            "tone": roles.STAFF_EVENT_TONE.get(e.kind, "neutral"),
            "date": e.happened_on.isoformat() if e.happened_on else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "title": e.title, "note": e.note,
            "score": e.score, "amount": e.amount, "minutes": e.minutes,
            "by": e.created_by,
        } for e in rows],
        "kinds": [{"key": k, "label": lbl, "tone": t}
                  for k, lbl, t in roles.STAFF_EVENTS],
    }


@app.post("/api/staff/{user_id}/events")
def add_staff_event(
    user_id: int,
    payload: schemas.StaffEventCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.kind not in roles.STAFF_EVENT_LABELS:
        raise HTTPException(400, "Noto'g'ri voqea turi")
    e = models.StaffEvent(
        user_id=user_id, kind=payload.kind,
        happened_on=payload.date or date.today(),
        end_date=payload.end_date, title=payload.title, note=payload.note,
        score=payload.score, amount=payload.amount, minutes=payload.minutes,
        created_by=user.full_name)
    db.add(e); db.commit(); db.refresh(e)
    audit.log(db, user, entity="user", action="update", entity_id=user_id,
              entity_label=emp.full_name, branch_id=emp.branch_id,
              field=roles.STAFF_EVENT_LABELS[payload.kind],
              new_value=payload.title or payload.note or "")
    db.commit()
    return {"id": e.id}


@app.delete("/api/staff/events/{event_id}")
def delete_staff_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    e = db.query(models.StaffEvent).get(event_id)
    if not e:
        raise HTTPException(404, "Topilmadi")
    db.delete(e); db.commit()
    return {"ok": True}


@app.get("/api/staff/{user_id}/card")
def staff_card(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Xodim kartasi. Maosh faqat SALARY_VIEW_ALL huquqi borlarga yoki
    odamning o'ziga ko'rinadi."""
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    if (user.role not in tuple(roles.HR_ACCESS)
            and user.role not in tuple(roles.SALARY_VIEW_ALL)
            and user.id != user_id):
        raise HTTPException(403, "Bu kartani ko'rishga ruxsatingiz yo'q")

    show_salary = (user.role in tuple(roles.SALARY_VIEW_ALL)
                   or user.id == user_id)

    events = (db.query(models.StaffEvent)
              .filter(models.StaffEvent.user_id == user_id).all())
    by_kind = {}
    for e in events:
        by_kind.setdefault(e.kind, []).append(e)

    def count(k):
        return len(by_kind.get(k, []))

    # Ta'til kunlari
    vac_days = 0
    for e in by_kind.get("vacation", []):
        if e.happened_on:
            end = e.end_date or e.happened_on
            vac_days += (end - e.happened_on).days + 1

    late_minutes = sum(e.minutes or 0 for e in by_kind.get("late", []))
    reviews = [e for e in by_kind.get("review", []) if e.score is not None]
    avg_review = round(sum(e.score for e in reviews) / len(reviews), 1) if reviews else None
    bonus_total = sum(e.amount or 0 for e in by_kind.get("bonus", []))

    # Ustoz bo'lsa - guruhlari va o'quvchilari
    teacher = (db.query(models.Teacher)
               .filter(models.Teacher.full_name == emp.full_name).first())
    groups, students = [], 0
    if teacher:
        gs = db.query(models.Group).filter(
            models.Group.teacher_id == teacher.id).all()
        for g in gs:
            n = db.query(models.Student).filter(
                models.Student.group_id == g.id,
                models.Student.status == "active").count()
            students += n
            groups.append({"id": g.id, "name": g.name, "students": n})

    manager = db.query(models.User).get(emp.manager_id) if emp.manager_id else None
    onb = _onboarding_rows(db, user_id)
    onb_done = sum(1 for r in onb if r["done"])

    return {
        "id": emp.id,
        "public_id": emp.public_id,
        "full_name": emp.full_name,
        "username": emp.username,
        "phone": emp.phone,
        "birth_date": emp.birth_date.isoformat() if emp.birth_date else None,
        "photo": emp.photo,
        "role": emp.role,
        "role_label": roles.UZ_LABELS.get(emp.role, emp.role),
        "position": emp.position or roles.UZ_LABELS.get(emp.role, emp.role),
        "branch_id": emp.branch_id,
        "branch": emp.branch.name if emp.branch else None,
        "manager_id": emp.manager_id,
        "manager": manager.full_name if manager else None,
        "hired_date": (emp.hired_date or
                       (emp.created_at.date() if emp.created_at else None)
                       ).isoformat() if (emp.hired_date or emp.created_at) else None,
        "is_active": bool(emp.is_active),
        "exit_type": emp.exit_type,
        "exit_type_label": roles.EXIT_TYPE_LABELS.get(emp.exit_type or "", None),
        "exit_reason": emp.exit_reason,
        "exit_date": emp.exit_date.isoformat() if emp.exit_date else None,
        # Maosh - faqat huquqi borga
        "salary": emp.fix_salary if show_salary else None,
        "salary_hidden": not show_salary,
        "bonus_total": bonus_total if show_salary else None,
        # KPI
        "groups": groups,
        "students": students,
        # Voqealar xulosasi
        "vacation_days": vac_days,
        "absences": count("absence"),
        "late_count": count("late"),
        "late_minutes": late_minutes,
        "trainings": count("training"),
        "reviews": len(reviews),
        "avg_review": avg_review,
        "disciplines": count("discipline"),
        "rewards": count("reward"),
        # Onboarding
        "onboarding": onb,
        "onboarding_done": onb_done,
        "onboarding_total": len(onb),
        "onboarding_percent": round(onb_done / len(onb) * 100) if onb else 0,
    }


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
    force: bool = False,
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
    # Sig'im va daraja mosligi - saqlashdan OLDIN tekshiriladi.
    _raise_if_blocked(_check_enrolment(db, s, g), force=force)
    # Darajasi hali yo'q bo'lsa - guruhnikidan olamiz.
    if not s.level:
        s.subject = s.subject or g.subject
        s.level = g.level
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
    # AVTOMAT: SMM'ga video olish vazifasi - hamma ma'lumoti bilan
    st = db.query(models.Student).get(student_id)
    if st:
        _smm_achievement_task(
            db, st,
            what=f"{roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind)}"
                 + (f" — {c.level}" if c.level else ""),
            detail=(f"Bali: {c.score}" if c.score else ""))
        db.commit()
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


# =====================================================================
#  Chegirmalar
#  Chegirma - bu pul. Shuning uchun xodim o'zi berolmaydi: so'raydi,
#  rahbar tasdiqlaydi, tizim muddatini kuzatadi.
# =====================================================================
def _discount_alive(d: models.Discount, on: date = None) -> bool:
    """Chegirma shu sanada amaldami."""
    on = on or date.today()
    if d.status != "active":
        return False
    if d.start_date and d.start_date > on:
        return False
    if d.end_date and d.end_date < on:
        return False
    return True


def _expire_discounts(db: Session) -> int:
    """AVTOMAT: muddati tugagan chegirmalarni yopadi va xodim ishdan
    ketgan bo'lsa "xodim farzandi" chegirmasini bekor qiladi.
    Hech kim qo'lda olib tashlashi shart emas."""
    today = date.today()
    n = 0
    rows = (db.query(models.Discount)
            .filter(models.Discount.status == "active").all())
    for d in rows:
        if d.end_date and d.end_date < today:
            d.status = "expired"
            n += 1
            continue
        if d.kind == "staff_child" and d.staff_user_id:
            emp = db.query(models.User).get(d.staff_user_id)
            if not emp or not emp.is_active:
                d.status = "cancelled"
                d.cancelled_reason = (
                    "Xodim ishdan ketdi — chegirma avtomat bekor qilindi")
                n += 1
    if n:
        db.commit()
    return n


def _student_discount_percent(db: Session, s: models.Student) -> float:
    """O'quvchining jami chegirma foizi: oilaviy (avtomat) + tasdiqlangan
    chegirmalar. Chegara MAX_TOTAL_DISCOUNT_PERCENT."""
    total = _family_discount_percent(db, s)
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == s.id,
                    models.Discount.status == "active").all())
    fee = s.group.monthly_fee if s.group else 0.0
    for d in rows:
        if d.kind == "family" or not _discount_alive(d):
            continue
        if d.percent:
            total += d.percent
        elif d.amount and fee:
            total += d.amount / fee * 100
    return min(roles.MAX_TOTAL_DISCOUNT_PERCENT, round(total, 2))


def _discount_out(db: Session, d: models.Discount) -> dict:
    ref = db.query(models.Student).get(d.referrer_student_id) if d.referrer_student_id else None
    emp = db.query(models.User).get(d.staff_user_id) if d.staff_user_id else None
    return {
        "id": d.id,
        "student_id": d.student_id,
        "kind": d.kind,
        "kind_label": roles.DISCOUNT_TYPE_LABELS.get(d.kind, d.kind),
        "percent": d.percent,
        "amount": d.amount,
        "reason": d.reason,
        "start_date": d.start_date.isoformat() if d.start_date else None,
        "end_date": d.end_date.isoformat() if d.end_date else None,
        "status": d.status,
        "status_label": roles.DISCOUNT_STATUS_LABELS.get(d.status, d.status),
        "alive": _discount_alive(d),
        "referrer_student_id": d.referrer_student_id,
        "referrer_name": ref.full_name if ref else None,
        "staff_user_id": d.staff_user_id,
        "staff_name": emp.full_name if emp else None,
        "requested_by": d.requested_by,
        "approved_by": d.approved_by,
        "approved_at": d.approved_at.isoformat() if d.approved_at else None,
        "cancelled_reason": d.cancelled_reason,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@app.get("/api/discounts")
def list_discounts(
    student_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    _expire_discounts(db)
    q = db.query(models.Discount)
    if student_id:
        q = q.filter(models.Discount.student_id == student_id)
    if status_filter:
        q = q.filter(models.Discount.status == status_filter)
    rows = q.order_by(models.Discount.created_at.desc()).all()

    # Filial kesimi - o'quvchi orqali
    if branch_id or not can_see_all_branches(user):
        allowed = {s.id for s in scope_to_branch(
            db.query(models.Student), models.Student, user, branch_id).all()}
        rows = [d for d in rows if d.student_id in allowed]

    out = []
    for d in rows:
        item = _discount_out(db, d)
        st = db.query(models.Student).get(d.student_id)
        item["student_name"] = st.full_name if st else "—"
        out.append(item)
    return {
        "rows": out,
        "types": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.DISCOUNT_TYPES],
        "statuses": [{"key": k, "label": lbl}
                     for k, lbl in roles.DISCOUNT_STATUSES],
        "max_percent": roles.MAX_TOTAL_DISCOUNT_PERCENT,
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "pending": sum(1 for d in rows if d.status == "pending"),
    }


@app.post("/api/discounts")
def create_discount(
    payload: schemas.DiscountCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    st = db.query(models.Student).get(payload.student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.kind not in roles.DISCOUNT_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri chegirma turi")
    if payload.kind in roles.AUTO_DISCOUNT_TYPES:
        raise HTTPException(
            400, "Oilaviy chegirmani tizim o'zi beradi — qo'lda qo'shilmaydi")
    if not (payload.percent or payload.amount):
        raise HTTPException(400, "Chegirma miqdorini kiriting")
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Sabab yozilishi shart")
    if payload.kind == "referral" and not payload.referrer_student_id:
        raise HTTPException(400, "Qaysi do'sti olib kelganini tanlang")
    if payload.kind == "staff_child" and not payload.staff_user_id:
        raise HTTPException(400, "Qaysi xodimning farzandi ekanini tanlang")

    # Jami chegirma chegaradan oshmasin
    now = _student_discount_percent(db, st)
    add = payload.percent or 0
    if not add and payload.amount and st.group and st.group.monthly_fee:
        add = payload.amount / st.group.monthly_fee * 100
    if now + add > roles.MAX_TOTAL_DISCOUNT_PERCENT:
        raise HTTPException(
            400,
            f"Jami chegirma {roles.MAX_TOTAL_DISCOUNT_PERCENT}% dan oshmasligi "
            f"kerak. Hozir {now:.0f}%, siz yana {add:.0f}% qo'shyapsiz.")

    d = models.Discount(
        student_id=payload.student_id,
        kind=payload.kind,
        percent=payload.percent,
        amount=payload.amount,
        reason=payload.reason.strip(),
        start_date=payload.start_date or date.today(),
        end_date=payload.end_date,
        referrer_student_id=payload.referrer_student_id,
        staff_user_id=payload.staff_user_id,
        requested_by=user.full_name,
        status="pending",
    )
    # Tasdiqlash huquqi bor odam o'zi so'rasa - darrov amalda.
    if user.role in roles.DISCOUNT_APPROVE:
        d.status = "active"
        d.approved_by = user.full_name
        d.approved_at = datetime.utcnow()
    db.add(d)
    db.commit()
    db.refresh(d)
    audit.log(db, user, entity="discount", action="create", entity_id=d.id,
              entity_label=st.full_name, branch_id=st.branch_id,
              new_value=f"{roles.DISCOUNT_TYPE_LABELS[d.kind]} "
                        f"{d.percent or d.amount}")
    db.commit()
    return _discount_out(db, d)


@app.post("/api/discounts/{discount_id}/approve")
def approve_discount(
    discount_id: int,
    payload: schemas.DiscountDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_APPROVE)),
):
    d = db.query(models.Discount).get(discount_id)
    if not d:
        raise HTTPException(404, "Chegirma topilmadi")
    if d.status not in ("pending", "rejected"):
        raise HTTPException(400, "Bu chegirma allaqachon hal qilingan")
    st = db.query(models.Student).get(d.student_id)
    d.status = "active" if payload.approve else "rejected"
    d.approved_by = user.full_name
    d.approved_at = datetime.utcnow()
    if not payload.approve:
        d.cancelled_reason = payload.reason
    db.commit()
    audit.log(db, user, entity="discount",
              action="approve" if payload.approve else "reject",
              entity_id=d.id, entity_label=st.full_name if st else "—",
              branch_id=st.branch_id if st else None,
              new_value=d.status)
    db.commit()
    return _discount_out(db, d)


@app.post("/api/discounts/{discount_id}/cancel")
def cancel_discount(
    discount_id: int,
    payload: schemas.DiscountDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_APPROVE)),
):
    d = db.query(models.Discount).get(discount_id)
    if not d:
        raise HTTPException(404, "Chegirma topilmadi")
    st = db.query(models.Student).get(d.student_id)
    d.status = "cancelled"
    d.cancelled_reason = payload.reason or "Bekor qilindi"
    db.commit()
    audit.log(db, user, entity="discount", action="cancel", entity_id=d.id,
              entity_label=st.full_name if st else "—",
              branch_id=st.branch_id if st else None,
              old_value="active", new_value="cancelled")
    db.commit()
    return _discount_out(db, d)


@app.get("/api/students/{student_id}/discounts")
def student_discounts(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    _expire_discounts(db)
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == student_id)
            .order_by(models.Discount.created_at.desc()).all())
    fam = _family_discount_percent(db, s)
    return {
        "rows": [_discount_out(db, d) for d in rows],
        "family_percent": fam,
        "total_percent": _student_discount_percent(db, s),
        "max_percent": roles.MAX_TOTAL_DISCOUNT_PERCENT,
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "types": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.DISCOUNT_TYPES
                  if k not in roles.AUTO_DISCOUNT_TYPES],
    }


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
    # Oylik chegirmasi bor bo'lsa - bir darsning narxi ham kamayadi.
    # Oilaviy + tasdiqlangan chegirmalarning hammasi hisobga olinadi.
    disc = _student_discount_percent(db, s)
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
        disc = _student_discount_percent(db, s)
        amount = lessons * (g.lesson_price or 0) * (100 - disc) / 100

        if commit and not already and amount > 0:
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (chegirma {disc}%)" if disc else ""),
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
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASH_ACCESS)),
):
    """To'lovlarni yig'ish foizi - HAR BIR O'QUVCHI bo'yicha alohida.

    Muhim nuqta: bir o'quvchi ortiqcha to'lasa, bu boshqasining qarzini
    yopmaydi. Shuning uchun har bir o'quvchida "qopланgan summa" shu
    oyning hisobidan oshmaydi, ortig'i esa KEYINGI OYGA o'tadi.

    Aks holda "225% bajarildi" degan raqam chiqib, to'lamagan ikki
    o'quvchi ko'rinmay qolardi."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)
    d0 = datetime.combine(start, datetime.min.time())
    d1 = datetime.combine(end, datetime.max.time())

    sq = scope_to_branch(db.query(models.Student), models.Student, user,
                         branch_id)
    students = sq.all()
    ids = [s.id for s in students]
    if not ids:
        return {"period": period, "charged": 0.0, "collected": 0.0,
                "percent": 0.0, "debt": 0.0, "students": 0,
                "paid_students": 0, "partial_students": 0,
                "unpaid_students": 0, "carry_in": 0.0, "carry_out": 0.0,
                "rows": [], "by_admin": []}

    # DIQQAT: hisoblangan pul qaysi oyga tegishli ekani "period" bilan
    # belgilanadi, yozuv qachon yaratilgani bilan emas. Aprel hisobini
    # may oyida yuritish mumkin - u baribir aprelniki bo'lib qoladi.
    # Haqiqiy pul esa aksincha: qachon kelgani muhim.
    charges, payments, opening = {}, {}, {}
    pay_rows = []

    for p in (db.query(models.Payment)
              .filter(models.Payment.student_id.in_(ids)).all()):
        sid = p.student_id
        if p.kind in ("charge", "discount"):
            per = p.period or (p.created_at.date().isoformat()[:7]
                               if p.created_at else period)
            if per == period:
                sign = 1 if p.kind == "charge" else -1
                charges[sid] = charges.get(sid, 0.0) + sign * abs(p.amount)
            elif per < period:
                # O'tgan davrlarning hisobi - ochilish balansiga kiradi
                opening[sid] = opening.get(sid, 0.0) - abs(p.amount)
        elif p.kind == "payment":
            if d0 <= p.created_at <= d1:
                payments[sid] = payments.get(sid, 0.0) + p.amount
                pay_rows.append(p)
            elif p.created_at < d0:
                opening[sid] = opening.get(sid, 0.0) + p.amount

    by_id = {s.id: s for s in students}
    rows = []
    tot_charged = tot_covered = tot_carry_in = tot_carry_out = 0.0
    paid_n = partial_n = unpaid_n = 0

    for sid in set(list(charges.keys()) + list(payments.keys())):
        ch = max(0.0, charges.get(sid, 0.0))
        pay = payments.get(sid, 0.0)
        carry_in = max(0.0, opening.get(sid, 0.0))     # o'tgan oydan qolgan pul
        old_debt = min(0.0, opening.get(sid, 0.0))     # o'tgan oydan qarz

        available = carry_in + pay
        covered = min(ch, available)                   # shu oyni qoplagani
        left = max(0.0, ch - covered)                  # shu oyda qolgan qarz
        carry_out = max(0.0, available - ch)           # keyingi oyga o'tadi

        if ch <= 0:
            continue
        tot_charged += ch
        tot_covered += covered
        tot_carry_in += carry_in
        tot_carry_out += carry_out

        if left <= 0.01:
            paid_n += 1
            state = "paid"
        elif covered > 0:
            partial_n += 1
            state = "partial"
        else:
            unpaid_n += 1
            state = "unpaid"

        st = by_id.get(sid)
        rows.append({
            "student_id": sid,
            "public_id": st.public_id if st else None,
            "full_name": st.full_name if st else "—",
            "group": st.group.name if st and st.group else None,
            "phone": st.phone if st else None,
            "charged": round(ch, 2),
            "paid": round(pay, 2),
            "carry_in": round(carry_in, 2),
            "covered": round(covered, 2),
            "left": round(left, 2),
            "carry_out": round(carry_out, 2),
            "old_debt": round(abs(old_debt), 2),
            "percent": round(covered / ch * 100, 1) if ch else 0.0,
            "state": state,
        })

    # To'lamaganlar tepada tursin - ular bilan ishlash kerak
    order = {"unpaid": 0, "partial": 1, "paid": 2}
    rows.sort(key=lambda r: (order[r["state"]], -r["left"]))

    # Kim yig'di - administrator kesimida
    by_admin = {}
    for p in pay_rows:
        who = p.created_by or "—"
        by_admin[who] = by_admin.get(who, 0.0) + p.amount
    admins = [{"name": k, "collected": round(v, 2)}
              for k, v in sorted(by_admin.items(), key=lambda kv: -kv[1])]

    return {
        "period": period,
        "charged": round(tot_charged, 2),
        # "collected" - shu oyning hisobiga QO'SHILGAN pul (ortiqchasi emas)
        "collected": round(tot_covered, 2),
        "cash_in": round(sum(p.amount for p in pay_rows), 2),
        "percent": round(tot_covered / tot_charged * 100, 1) if tot_charged else 0.0,
        "debt": round(tot_charged - tot_covered, 2),
        "carry_in": round(tot_carry_in, 2),
        "carry_out": round(tot_carry_out, 2),
        "students": len(rows),
        "paid_students": paid_n,
        "partial_students": partial_n,
        "unpaid_students": unpaid_n,
        "rows": rows,
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
#  FILIAL REYTINGI
#  Filialni faqat tushum bilan baholash - eng katta xato. Ko'p pul
#  yig'ib, o'quvchini yo'qotayotgan filial "yaxshi" ko'rinib qoladi.
#  Shuning uchun 7 o'lchov, har birining o'z og'irligi bilan.
# =====================================================================
def _rating_weights(db: Session) -> dict:
    """Og'irliklar. Bitta filialda saqlanadi (hammasi uchun bir xil),
    bo'sh bo'lsa standart taqsimot."""
    b = db.query(models.Branch).filter(
        models.Branch.rating_weights.isnot(None)).first()
    if b and b.rating_weights:
        try:
            w = json.loads(b.rating_weights)
            if isinstance(w, dict) and w:
                return {k: float(w.get(k, v))
                        for k, v in roles.BRANCH_RATING_DEFAULT.items()}
        except Exception:
            pass
    return dict(roles.BRANCH_RATING_DEFAULT)


def _scale(value, lo, hi, higher_is_better=True) -> float:
    """Qiymatni 0-100 shkalaga o'tkazadi. lo va hi - kutilgan chegaralar."""
    if value is None:
        return 50.0     # ma'lumot yo'q - o'rtacha deb olamiz
    if hi == lo:
        return 50.0
    x = (value - lo) / (hi - lo) * 100
    x = max(0.0, min(100.0, x))
    return x if higher_is_better else 100.0 - x


@app.get("/api/ceo/branch-rating")
def branch_rating(
    months: int = 3,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Filiallar reytingi. Har bir o'lchov 0-100 balga keltiriladi,
    keyin og'irligiga ko'paytiriladi."""
    base = ceo_branches(months=months, db=db, user=user)
    weights = _rating_weights(db)
    total_w = sum(weights.values()) or 1

    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)

    # Akademik natija: filial bo'yicha imtihon o'rtachasi
    academic = {}
    exams = (db.query(models.Exam, models.Group)
             .join(models.Group, models.Exam.group_id == models.Group.id)
             .filter(models.Exam.date >= start, models.Exam.date <= end).all())
    ex_ids = {e.id: g.branch_id for e, g in exams}
    if ex_ids:
        for r in db.query(models.ExamResult).filter(
                models.ExamResult.exam_id.in_(list(ex_ids))).all():
            if r.absent or r.percent is None:
                continue
            bid = ex_ids.get(r.exam_id)
            academic.setdefault(bid, []).append(r.percent)

    # Ota-onalar mamnunligi: shikoyatlar soni (kam bo'lsa yaxshi)
    complaints = {}
    for c in db.query(models.Complaint).all():
        if c.created_at and c.created_at.date() >= start:
            complaints[c.branch_id] = complaints.get(c.branch_id, 0) + 1

    # Operatsion intizom: dars kunlari/vaqti belgilanmagan guruhlar va
    # yopilmagan vazifalar
    sloppy = {}
    for g in db.query(models.Group).all():
        if not g.lesson_days or not g.lesson_time:
            sloppy[g.branch_id] = sloppy.get(g.branch_id, 0) + 1
    late_tasks = {}
    for t in db.query(models.Task).filter(
            ~models.Task.status.in_(roles.TASK_CLOSED)).all():
        if t.deadline and t.deadline < today:
            late_tasks[t.branch_id] = late_tasks.get(t.branch_id, 0) + 1

    rows = []
    for r in base["rows"]:
        bid = r["branch_id"]
        marks = academic.get(bid, [])
        acad = round(sum(marks) / len(marks), 1) if marks else None
        n_active = r["active"] or 1

        # Har bir o'lchov 0-100 ballga
        scores = {
            # Rentabellik -20%..+40% oralig'ida baholanadi
            "finance": _scale(r["margin"], -20, 40),
            # Churn 0..20% - kam bo'lsa yaxshi
            "retention": _scale(r["churn"], 0, 20, higher_is_better=False),
            # Konversiya 0..50%
            "sales": _scale(r["conversion"], 0, 50),
            # Imtihon o'rtachasi 50..90%
            "academic": _scale(acad, 50, 90),
            # Bir o'quvchiga to'g'ri keladigan qarz 0..300 ming
            "debt": _scale(r["debt"] / n_active, 0, 300000,
                           higher_is_better=False),
            # 100 o'quvchiga shikoyat 0..10 ta
            "parents": _scale(complaints.get(bid, 0) / n_active * 100, 0, 10,
                              higher_is_better=False),
            # Tartibsizlik: to'ldirilmagan guruh + kechikkan vazifa
            "discipline": _scale(
                sloppy.get(bid, 0) + late_tasks.get(bid, 0), 0, 10,
                higher_is_better=False),
        }
        total = sum(scores[k] * weights.get(k, 0) for k in scores) / total_w
        key, label = roles.branch_grade(total)
        rows.append({
            "branch_id": bid,
            "branch": r["branch"],
            "score": round(total, 1),
            "grade": key,
            "grade_label": label,
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "raw": {
                "margin": r["margin"], "churn": r["churn"],
                "conversion": r["conversion"], "academic": acad,
                "debt_per_student": round(r["debt"] / n_active),
                "complaints": complaints.get(bid, 0),
                "issues": sloppy.get(bid, 0) + late_tasks.get(bid, 0),
                "active": r["active"], "income": r["income"],
                "profit": r["profit"],
            },
        })
    rows.sort(key=lambda x: -x["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    return {
        "months": months,
        "period": base["period"],
        "rows": rows,
        "weights": weights,
        "dimensions": [{"key": k, "label": lbl, "weight": weights.get(k, w)}
                       for k, lbl, w in roles.BRANCH_RATING_WEIGHTS],
        "grades": [{"key": k, "label": lbl, "min": lim}
                   for lim, k, lbl in roles.BRANCH_GRADES],
    }


@app.put("/api/ceo/branch-rating/weights")
def set_rating_weights(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """Og'irliklarni o'zgartirish. Strategiya o'zgarsa - foizlar ham."""
    w = {}
    for k in roles.BRANCH_RATING_DEFAULT:
        try:
            w[k] = max(0.0, float(payload.get(k, roles.BRANCH_RATING_DEFAULT[k])))
        except Exception:
            w[k] = float(roles.BRANCH_RATING_DEFAULT[k])
    if sum(w.values()) <= 0:
        raise HTTPException(400, "Og'irliklar yig'indisi 0 bo'lishi mumkin emas")
    for b in db.query(models.Branch).all():
        b.rating_weights = json.dumps(w)
    db.commit()
    audit.log(db, user, entity="branch", action="update", entity_id=0,
              entity_label="Filial reytingi",
              field="Og'irliklar", new_value=json.dumps(w))
    db.commit()
    return {"weights": w}


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


# =====================================================================
#  MA'LUMOTNOMALAR  -  tanlanadigan ro'yxatlar
# =====================================================================
@app.get("/api/reference")
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


# =====================================================================
#  DARS JADVALI
# =====================================================================
@app.get("/api/timetable")
def timetable(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Haftalik dars jadvali: qaysi kun, qaysi vaqt, qaysi guruh,
    qaysi ustoz, qaysi xona. Administrator uchun kunlik ish shu
    jadvaldan boshlanadi."""
    gq = scope_to_branch(db.query(models.Group), models.Group, user, branch_id)
    groups = gq.all()
    rooms = {r.id: r for r in db.query(models.Room).all()}

    counts = {}
    for st in scope_to_branch(db.query(models.Student), models.Student,
                              user, branch_id).all():
        if st.status == "active" and st.group_id:
            counts[st.group_id] = counts.get(st.group_id, 0) + 1

    items = []
    for g in groups:
        days = [d.strip() for d in (g.lesson_days or "").split(",") if d.strip()]
        if not days:
            continue
        room = rooms.get(g.room_id)
        items.append({
            "group_id": g.id, "group": g.name,
            "public_id": g.public_id,
            "subject": g.subject,
            "subject_label": dict(roles.SUBJECTS).get(g.subject or "", ""),
            "level": g.level,
            "level_label": dict(roles.SUBJECT_LEVELS.get(g.subject or "", []))
                           .get(g.level or "", g.level or ""),
            "teacher": g.teacher.full_name if g.teacher else None,
            "branch": g.branch.name if g.branch else None,
            "room": room.name if room else g.room,
            "capacity": _group_capacity(g, rooms),
            "students": counts.get(g.id, 0),
            "days": days,
            "start": g.lesson_time,
            "end": roles.lesson_end_time(g.lesson_time or ""),
            "time_label": roles.lesson_time_range(g.lesson_time),
            "start_date": g.start_date.isoformat() if g.start_date else None,
            "end_date": g.end_date.isoformat() if g.end_date else None,
        })

    # Kun -> vaqt bo'yicha guruhlangan ko'rinish
    by_day = {}
    for it in items:
        for d in it["days"]:
            by_day.setdefault(d, []).append(it)
    for d in by_day:
        by_day[d].sort(key=lambda x: (x["start"] or "99:99", x["group"]))

    # Xona bandligi: bir vaqtda bir xonada ikki guruh bo'lsa - to'qnashuv
    clashes = []
    seen = {}
    for it in items:
        if not it["room"] or not it["start"]:
            continue
        for d in it["days"]:
            key = (d, it["room"], it["start"])
            if key in seen:
                clashes.append({
                    "day": d, "room": it["room"], "time": it["time_label"],
                    "groups": [seen[key], it["group"]],
                })
            else:
                seen[key] = it["group"]

    return {
        "days": [{"key": k, "label": lbl, "short": sh}
                 for k, lbl, sh in roles.WEEKDAYS],
        "by_day": by_day,
        "items": sorted(items, key=lambda x: (x["start"] or "99:99", x["group"])),
        "no_schedule": [{"id": g.id, "name": g.name} for g in groups
                        if not (g.lesson_days or "").strip()],
        "clashes": clashes,
    }


# =====================================================================
#  ARXIV
# =====================================================================
@app.get("/api/archive/students")
def archive_students(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Ketgan o'quvchilar - pul munosabati bo'yicha uch guruhda.

    Bu shunchaki ro'yxat emas: kimdan pul olish kerakligi va kimga
    qaytarish kerakligi ko'rinib turishi kerak, aks holda ketgan
    o'quvchining qarzi unutilib ketadi."""
    sq = scope_to_branch(db.query(models.Student), models.Student, user,
                         branch_id).filter(models.Student.status == "archived")
    rows = []
    for s in sq.all():
        bal = student_balance(db, s.id)
        if bal < -0.01:
            grp = "debtor"
        elif bal > 0.01:
            grp = "credit"
        else:
            grp = "clear"
        rows.append({
            "id": s.id, "public_id": s.public_id, "full_name": s.full_name,
            "phone": s.phone, "parent_phone": s.parent_phone,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "enrolled_date": s.enrolled_date.isoformat() if s.enrolled_date else None,
            "left_date": s.left_date.isoformat() if s.left_date else None,
            "months": (_months_between(s.enrolled_date, s.left_date or date.today())
                       if s.enrolled_date else None),
            "balance": round(bal, 2),
            "amount": round(abs(bal), 2),
            "group_key": grp,
        })
    rows.sort(key=lambda r: (-r["amount"], r["full_name"]))

    groups = []
    for key, label, hint in roles.ARCHIVE_GROUPS:
        part = [r for r in rows if r["group_key"] == key]
        groups.append({
            "key": key, "label": label, "hint": hint,
            "count": len(part),
            "total": round(sum(r["amount"] for r in part), 2),
        })
    return {"groups": groups, "rows": rows, "total": len(rows)}


@app.get("/api/archive/staff")
def archive_staff(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    """Ishdan bo'shagan xodimlar - qanday ajrashilgani bo'yicha.
    Qayta ishga olish masalasida shu ro'yxat hal qiluvchi."""
    q = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 0)
    rows = [{
        "id": u.id, "public_id": u.public_id, "full_name": u.full_name,
        "username": u.username, "role": u.role,
        "role_label": roles.UZ_LABELS.get(u.role, u.role),
        "branch": u.branch.name if u.branch else None,
        "exit_type": u.exit_type or "neutral",
        "exit_label": roles.EXIT_TYPE_LABELS.get(u.exit_type or "neutral",
                                                 "Neytral"),
        "exit_reason": u.exit_reason,
        "exit_date": u.exit_date.isoformat() if u.exit_date else None,
    } for u in q.all()]
    rows.sort(key=lambda r: (r["exit_date"] or "", r["full_name"]), reverse=True)

    groups = []
    for key, label, hint in roles.EXIT_TYPES:
        groups.append({
            "key": key, "label": label, "hint": hint,
            "count": sum(1 for r in rows if r["exit_type"] == key),
        })
    return {"groups": groups, "rows": rows, "total": len(rows)}


@app.put("/api/archive/staff/{user_id}")
def set_exit_type(
    user_id: int,
    payload: schemas.ExitTypeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.exit_type not in roles.EXIT_TYPE_LABELS:
        raise HTTPException(400, "Noma'lum toifa")
    old = u.exit_type
    u.exit_type = payload.exit_type
    u.exit_reason = payload.exit_reason
    if not u.exit_date:
        u.exit_date = date.today()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field="exit_type",
              old_value=old, new_value=u.exit_type, note=payload.exit_reason,
              branch_id=u.branch_id, commit=True)
    return {"ok": True}


# =====================================================================
#  MANZIL VA MAKTAB KESIMIDA STATISTIKA
# =====================================================================
@app.get("/api/analytics/geography")
def analytics_geography(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Qaysi mahalladan va qaysi maktabdan ko'proq o'quvchi kelyapti.

    Reklamani qayerga qo'yish kerakligini shu ko'rsatadi: eng ko'p
    lid keladigan mahalla emas, eng ko'p O'QUVCHIGA aylanadigan
    mahalla muhim."""
    since = (date(2000, 1, 1) if months == 0
             else date.today() - timedelta(days=int(max(1, months) * 30.44)))
    lq = scope_to_branch(db.query(models.Lead), models.Lead, user,
                         branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time()))
    leads = lq.all()

    def agg(attr: str, known: list):
        acc = {}
        for l in leads:
            v = (getattr(l, attr) or "").strip()
            key = v if v else "—"
            d = acc.setdefault(key, {"leads": 0, "converted": 0})
            d["leads"] += 1
            if l.stage == "converted":
                d["converted"] += 1
        rows = [{
            "name": k, "leads": v["leads"], "converted": v["converted"],
            "conversion": round(v["converted"] / v["leads"] * 100, 1)
                          if v["leads"] else 0.0,
            "known": k in known,
        } for k, v in acc.items()]
        rows.sort(key=lambda r: (-r["converted"], -r["leads"]))
        return rows

    bname = None
    bid = branch_id or user.branch_id
    if bid:
        b = db.query(models.Branch).get(bid)
        bname = b.name if b else None

    areas = agg("address", roles.areas_for_branch(bname))
    schools = agg("school", roles.SCHOOLS)

    return {
        "months": months,
        "total_leads": len(leads),
        "areas": areas,
        "schools": schools,
        "top_area": areas[0] if areas and areas[0]["name"] != "—" else None,
        "top_school": schools[0] if schools and schools[0]["name"] != "—" else None,
        # Ro'yxatdan tanlanmagan, qo'lda yozilgan qiymatlar soni
        "free_text_areas": sum(1 for a in areas if not a["known"] and a["name"] != "—"),
        "free_text_schools": sum(1 for s in schools if not s["known"] and s["name"] != "—"),
    }


# =====================================================================
#  VAZIFALAR VA ICHKI NAZORAT
#  Majlisdagi qaror shu yerga tushmasa - majlis choy ichishga aylanadi:
#  choy qoladi, natija qolmaydi.
# =====================================================================
def _task_checklist(t: models.Task) -> list:
    try:
        rows = json.loads(t.checklist or "[]")
        return [{"text": str(r.get("text", "")), "done": bool(r.get("done"))}
                for r in rows if isinstance(r, dict)]
    except Exception:
        return []


def _task_status(t: models.Task) -> str:
    """AVTOMAT: muddati o'tgan va yopilmagan vazifa "Kechikdi" bo'ladi.
    Hech kim qo'lda belgilashi shart emas."""
    if t.status in roles.TASK_CLOSED:
        return t.status
    if t.deadline and t.deadline < date.today():
        return "late"
    return t.status


def _task_out(db: Session, t: models.Task) -> dict:
    chk = _task_checklist(t)
    st = _task_status(t)
    days = (t.deadline - date.today()).days if t.deadline else None
    return {
        "id": t.id,
        "public_id": t.public_id,
        "title": t.title,
        "description": t.description,
        "assignee_id": t.assignee_id,
        "assignee": t.assignee.full_name if t.assignee else None,
        "watcher_id": t.watcher_id,
        "watcher": t.watcher.full_name if t.watcher else None,
        "branch_id": t.branch_id,
        "branch": t.branch.name if t.branch else None,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "days_left": days,
        "overdue": bool(t.deadline and t.deadline < date.today()
                        and t.status not in roles.TASK_CLOSED),
        "priority": t.priority,
        "priority_label": roles.TASK_PRIORITY_LABELS.get(t.priority, t.priority),
        "priority_rank": roles.TASK_PRIORITY_RANK.get(t.priority, 2),
        "status": st,
        "status_label": roles.TASK_STATUS_LABELS.get(st, st),
        "status_tone": roles.TASK_STATUS_TONE.get(st, "slate"),
        "stored_status": t.status,
        "source": t.source,
        "source_label": roles.TASK_SOURCE_LABELS.get(t.source, t.source),
        "meeting": t.meeting,
        "checklist": chk,
        "checklist_done": sum(1 for c in chk if c["done"]),
        "checklist_total": len(chk),
        "attachment_id": t.attachment_id,
        "result": t.result,
        "delay_reason": t.delay_reason,
        "done_at": t.done_at.isoformat() if t.done_at else None,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@app.get("/api/tasks")
def list_tasks(
    status_filter: Optional[str] = None,
    assignee_id: Optional[int] = None,
    mine: bool = False,
    branch_id: Optional[int] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    backfill_missing_ids(db, "task", models.Task)
    q = scope_to_branch(db.query(models.Task), models.Task, user, branch_id)

    # Vazifalarni boshqarish huquqi bo'lmagan odam faqat o'ziga tegishlini
    # ko'radi - boshqalarning vazifasi uni chalg'itmaydi.
    if user.role not in tuple(roles.TASK_MANAGE) or mine:
        q = q.filter((models.Task.assignee_id == user.id)
                     | (models.Task.watcher_id == user.id))
    if assignee_id:
        q = q.filter(models.Task.assignee_id == assignee_id)
    if source:
        q = q.filter(models.Task.source == source)

    rows = [_task_out(db, t) for t in q.all()]
    if status_filter:
        rows = [r for r in rows if r["status"] == status_filter]

    # Muhimi tepada: kechikkan → shoshilinch → yaqin muddat
    rows.sort(key=lambda r: (
        0 if r["overdue"] else 1,
        -r["priority_rank"],
        r["days_left"] if r["days_left"] is not None else 9999,
    ))

    counts = {}
    for t in q.all():
        st = _task_status(t)
        counts[st] = counts.get(st, 0) + 1

    return {
        "rows": rows,
        "counts": counts,
        "statuses": [{"key": k, "label": lbl, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, lbl, t in roles.TASK_STATUSES],
        "priorities": [{"key": k, "label": lbl}
                       for k, lbl, _ in roles.TASK_PRIORITIES],
        "sources": [{"key": k, "label": lbl} for k, lbl in roles.TASK_SOURCES],
        "can_manage": user.role in tuple(roles.TASK_MANAGE),
        "overdue": sum(1 for r in rows if r["overdue"]),
        "open": sum(1 for r in rows if r["status"] not in roles.TASK_CLOSED),
    }


@app.post("/api/tasks")
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    if not (payload.title or "").strip():
        raise HTTPException(400, "Vazifa nomini yozing")
    if payload.priority not in roles.TASK_PRIORITY_LABELS:
        raise HTTPException(400, "Noto'g'ri ustuvorlik")
    if payload.source not in roles.TASK_SOURCE_LABELS:
        raise HTTPException(400, "Noto'g'ri manba")

    bid = payload.branch_id
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        bid = user.branch_id

    t = models.Task(
        title=payload.title.strip(),
        description=payload.description,
        assignee_id=payload.assignee_id,
        watcher_id=payload.watcher_id,
        branch_id=bid,
        deadline=payload.deadline,
        priority=payload.priority,
        source=payload.source,
        meeting=payload.meeting,
        checklist=json.dumps([{"text": x, "done": False}
                              for x in (payload.checklist or []) if x.strip()]),
        created_by=user.full_name,
    )
    db.add(t); db.commit(); db.refresh(t)
    _ensure_public_id(db, "task", t)
    audit.log(db, user, entity="task", action="create", entity_id=t.id,
              entity_label=t.title, branch_id=t.branch_id, new_value=t.title)
    db.commit(); db.refresh(t)
    return _task_out(db, t)


@app.put("/api/tasks/{task_id}")
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    t = db.query(models.Task).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    is_owner = t.assignee_id == user.id or t.watcher_id == user.id
    if user.role not in tuple(roles.TASK_MANAGE) and not is_owner:
        raise HTTPException(403, "Bu vazifa sizga tegishli emas")

    fields = payload.model_dump(exclude_unset=True)

    # Mas'ul odam vazifani boshqasiga o'tkazib yubormasligi kerak -
    # buni faqat rahbar qila oladi.
    if user.role not in tuple(roles.TASK_MANAGE):
        for k in ("assignee_id", "watcher_id", "deadline", "priority",
                  "branch_id"):
            fields.pop(k, None)

    if "status" in fields:
        new = fields["status"]
        if new not in roles.TASK_STATUS_LABELS:
            raise HTTPException(400, "Noto'g'ri status")
        # "Kechikdi" - tizim o'zi qo'yadigan status, qo'lda tanlanmaydi.
        if new == "late":
            raise HTTPException(
                400, "\"Kechikdi\" statusini tizim o'zi qo'yadi")
        # Muddati o'tib bajarilyaptimi - sabab so'raladi.
        if (new == "done" and t.deadline and t.deadline < date.today()
                and not (fields.get("delay_reason") or t.delay_reason)):
            raise HTTPException(
                400, "Muddat o'tgan — kechikish sababini yozing")
        if new == "done":
            fields.setdefault("result", t.result)
            t.done_at = datetime.utcnow()
        elif t.status == "done":
            t.done_at = None

    if "checklist" in fields:
        rows = fields.pop("checklist") or []
        t.checklist = json.dumps([
            {"text": str(r.get("text", "")), "done": bool(r.get("done"))}
            for r in rows if isinstance(r, dict)])

    audit.log_changes(db, user, entity="task", obj=t,
                      changes={k: v for k, v in fields.items()
                               if k in ("status", "assignee_id", "deadline",
                                        "priority")})
    for k, v in fields.items():
        setattr(t, k, v)
    db.commit(); db.refresh(t)
    return _task_out(db, t)


@app.delete("/api/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_MANAGE)),
):
    t = db.query(models.Task).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    audit.log(db, user, entity="task", action="delete", entity_id=t.id,
              entity_label=t.title, branch_id=t.branch_id, old_value=t.title)
    db.delete(t); db.commit()
    return {"ok": True}


@app.post("/api/tasks/from-meeting")
def tasks_from_meeting(
    payload: schemas.MeetingDecisions,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_MANAGE)),
):
    """Majlis qarorlarini vazifaga aylantirish. Bir majlisdan 5 ta qaror
    chiqsa - 5 ta vazifa, har biri mas'uli va muddati bilan."""
    if not payload.decisions:
        raise HTTPException(400, "Qarorlar ro'yxati bo'sh")
    made = []
    for d in payload.decisions:
        if not (d.title or "").strip():
            continue
        t = models.Task(
            title=d.title.strip(),
            description=d.description,
            assignee_id=d.assignee_id,
            watcher_id=payload.watcher_id,
            branch_id=payload.branch_id,
            deadline=d.deadline or payload.deadline,
            priority=d.priority or "normal",
            source="meeting",
            meeting=payload.meeting,
            created_by=user.full_name,
        )
        db.add(t); db.flush()
        _ensure_public_id(db, "task", t)
        made.append(t)
    db.commit()
    return {"created": len(made),
            "rows": [_task_out(db, t) for t in made]}


# =====================================================================
#  OMBOR VA AKTIVLAR
# =====================================================================
def _next_inventory_no(db: Session, kind: str) -> str:
    """Inventar raqami: "AC-0007". Turi bo'yicha ketma-ket boradi."""
    prefix = {
        "computer": "PC", "laptop": "NB", "tv": "TV", "projector": "PR",
        "printer": "PT", "furniture": "FR", "camera": "CM",
        "phone": "PH", "ac": "AC", "router": "RT", "other": "OT",
    }.get(kind, "OT")
    n = db.query(models.Asset).filter(models.Asset.kind == kind).count() + 1
    while db.query(models.Asset).filter(
            models.Asset.inventory_no == f"{prefix}-{n:04d}").first():
        n += 1
    return f"{prefix}-{n:04d}"


def _asset_out(db: Session, a: models.Asset) -> dict:
    reps = sorted(a.repairs, key=lambda r: r.happened_on or date.min,
                  reverse=True)
    return {
        "id": a.id,
        "inventory_no": a.inventory_no,
        "name": a.name,
        "kind": a.kind,
        "kind_label": roles.ASSET_TYPE_LABELS.get(a.kind, a.kind),
        "branch_id": a.branch_id,
        "branch": a.branch.name if a.branch else None,
        "room_id": a.room_id,
        "room": a.room.name if a.room else None,
        "responsible_id": a.responsible_id,
        "responsible": a.responsible.full_name if a.responsible else None,
        "purchased_on": a.purchased_on.isoformat() if a.purchased_on else None,
        "price": a.price,
        "condition": a.condition,
        "condition_label": roles.ASSET_CONDITION_LABELS.get(a.condition, a.condition),
        "condition_tone": roles.ASSET_CONDITION_TONE.get(a.condition, "slate"),
        "warranty_until": a.warranty_until.isoformat() if a.warranty_until else None,
        "warranty_active": bool(a.warranty_until and a.warranty_until >= date.today()),
        "serial_no": a.serial_no,
        "photo": a.photo,
        "note": a.note,
        "written_off_on": a.written_off_on.isoformat() if a.written_off_on else None,
        "repairs": [{
            "id": r.id,
            "date": r.happened_on.isoformat() if r.happened_on else None,
            "cost": r.cost, "vendor": r.vendor, "note": r.note,
        } for r in reps],
        "repair_count": len(reps),
        "repair_cost": round(sum(r.cost or 0 for r in reps), 2),
        # Ta'mir narxi jihoz narxining yarmidan oshsa - almashtirish arzon.
        "replace_hint": bool(
            a.price and sum(r.cost or 0 for r in reps) > a.price * 0.5),
    }


@app.get("/api/assets")
def list_assets(
    branch_id: Optional[int] = None,
    kind: Optional[str] = None,
    condition: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    q = scope_to_branch(db.query(models.Asset), models.Asset, user, branch_id)
    if kind:
        q = q.filter(models.Asset.kind == kind)
    if condition:
        q = q.filter(models.Asset.condition == condition)
    rows = [_asset_out(db, a) for a in q.order_by(models.Asset.inventory_no).all()]

    return {
        "rows": rows,
        "total_value": round(sum(r["price"] or 0 for r in rows), 2),
        "count": len(rows),
        "needs_attention": sum(1 for r in rows
                               if r["condition"] in ("repair", "broken")),
        "kinds": [{"key": k, "label": lbl,
                   "count": sum(1 for r in rows if r["kind"] == k)}
                  for k, lbl in roles.ASSET_TYPES],
        "conditions": [{"key": k, "label": lbl, "tone": t,
                        "count": sum(1 for r in rows if r["condition"] == k)}
                       for k, lbl, t in roles.ASSET_CONDITIONS],
        "can_edit": user.role in tuple(roles.INVENTORY_ACCESS),
    }


@app.post("/api/assets")
def create_asset(
    payload: schemas.AssetCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    if payload.kind not in roles.ASSET_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri aktiv turi")
    if payload.condition not in roles.ASSET_CONDITION_LABELS:
        raise HTTPException(400, "Noto'g'ri holat")
    if payload.photo and len(payload.photo) > roles.ATTACHMENT_MAX_BYTES:
        raise HTTPException(400, "Rasm juda katta (3 MB dan oshmasin)")

    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    a = models.Asset(**data)
    a.inventory_no = a.inventory_no or _next_inventory_no(db, a.kind)
    db.add(a); db.commit(); db.refresh(a)
    audit.log(db, user, entity="asset", action="create", entity_id=a.id,
              entity_label=f"{a.inventory_no} {a.name}", branch_id=a.branch_id,
              new_value=a.name)
    db.commit()
    return _asset_out(db, a)


@app.put("/api/assets/{asset_id}")
def update_asset(
    asset_id: int,
    payload: schemas.AssetUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    fields = payload.model_dump(exclude_unset=True)
    if fields.get("photo") and len(fields["photo"]) > roles.ATTACHMENT_MAX_BYTES:
        raise HTTPException(400, "Rasm juda katta (3 MB dan oshmasin)")
    audit.log_changes(db, user, entity="asset", obj=a,
                      changes={k: v for k, v in fields.items()
                               if k in ("condition", "responsible_id",
                                        "room_id", "branch_id")})
    for k, v in fields.items():
        setattr(a, k, v)
    # Hisobdan chiqarilgan bo'lsa sanani avtomat qo'yamiz.
    if a.condition == "written_off" and not a.written_off_on:
        a.written_off_on = date.today()
    elif a.condition != "written_off":
        a.written_off_on = None
    db.commit(); db.refresh(a)
    return _asset_out(db, a)


@app.delete("/api/assets/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    audit.log(db, user, entity="asset", action="delete", entity_id=a.id,
              entity_label=f"{a.inventory_no} {a.name}",
              branch_id=a.branch_id, old_value=a.name)
    db.delete(a); db.commit()
    return {"ok": True}


@app.post("/api/assets/{asset_id}/repairs")
def add_repair(
    asset_id: int,
    payload: schemas.RepairCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    a = db.query(models.Asset).get(asset_id)
    if not a:
        raise HTTPException(404, "Aktiv topilmadi")
    r = models.AssetRepair(
        asset_id=asset_id, happened_on=payload.date or date.today(),
        cost=payload.cost or 0, vendor=payload.vendor, note=payload.note,
        created_by=user.full_name)
    db.add(r)
    # Ta'mirga berilgan jihoz "ta'mirda" bo'ladi.
    if a.condition not in ("written_off",):
        a.condition = "repair"
    db.commit(); db.refresh(a)
    return _asset_out(db, a)


@app.post("/api/assets/repairs/{repair_id}/done")
def finish_repair(
    repair_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    r = db.query(models.AssetRepair).get(repair_id)
    if not r:
        raise HTTPException(404, "Topilmadi")
    a = db.query(models.Asset).get(r.asset_id)
    if a and a.condition == "repair":
        a.condition = "good"
    db.commit()
    return _asset_out(db, a) if a else {"ok": True}


# ---- Sarflanadigan mahsulotlar -----------------------------------------
def _check_stock(db: Session, c: models.Consumable) -> models.PurchaseRequest | None:
    """AVTOMAT: qoldiq minimaldan pastga tushsa xarid so'rovi yaratiladi.
    Ochiq so'rov allaqachon bo'lsa takror yaratilmaydi - shunda ro'yxat
    bir xil so'rovlar bilan to'lib ketmaydi."""
    if c.min_qty is None or c.qty > c.min_qty:
        return None
    exists = (db.query(models.PurchaseRequest)
              .filter(models.PurchaseRequest.consumable_id == c.id,
                      models.PurchaseRequest.status == "open").first())
    if exists:
        return exists
    # Minimalning ikki barobariga to'ldiramiz - tez-tez so'rov qilmaslik uchun
    need = max(1.0, (c.min_qty or 1) * 2 - c.qty)
    pr = models.PurchaseRequest(
        consumable_id=c.id, qty=need, auto=1,
        note=f"Qoldiq {c.qty} {c.unit or 'dona'}, minimal {c.min_qty}")
    db.add(pr)
    return pr


def _consumable_out(db: Session, c: models.Consumable) -> dict:
    low = c.min_qty is not None and c.qty <= c.min_qty
    open_pr = (db.query(models.PurchaseRequest)
               .filter(models.PurchaseRequest.consumable_id == c.id,
                       models.PurchaseRequest.status == "open").first())
    return {
        "id": c.id,
        "name": c.name,
        "kind": c.kind,
        "kind_label": roles.CONSUMABLE_TYPE_LABELS.get(c.kind, c.kind),
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "qty": c.qty,
        "min_qty": c.min_qty,
        "unit": c.unit or roles.CONSUMABLE_UNITS.get(c.kind, "dona"),
        "unit_price": c.unit_price,
        "value": round((c.qty or 0) * (c.unit_price or 0), 2),
        "low": low,
        "note": c.note,
        "request_id": open_pr.id if open_pr else None,
        "request_qty": open_pr.qty if open_pr else None,
    }


@app.get("/api/consumables")
def list_consumables(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    q = scope_to_branch(db.query(models.Consumable), models.Consumable,
                        user, branch_id)
    items = q.order_by(models.Consumable.name).all()
    # Har safar ko'rilganda qoldiq tekshiriladi - so'rov o'zi paydo bo'ladi.
    for c in items:
        _check_stock(db, c)
    db.commit()

    rows = [_consumable_out(db, c) for c in items]
    reqs = (db.query(models.PurchaseRequest)
            .filter(models.PurchaseRequest.status == "open").all())
    ids = {c.id for c in items}
    reqs = [r for r in reqs if r.consumable_id in ids]

    return {
        "rows": rows,
        "low_count": sum(1 for r in rows if r["low"]),
        "total_value": round(sum(r["value"] for r in rows), 2),
        "kinds": [{"key": k, "label": lbl, "unit": u}
                  for k, lbl, u in roles.CONSUMABLE_TYPES],
        "reasons": [{"key": k, "label": lbl}
                    for k, lbl in roles.STOCK_MOVE_REASONS],
        "requests": [{
            "id": r.id,
            "consumable_id": r.consumable_id,
            "name": next((c.name for c in items if c.id == r.consumable_id), "—"),
            "qty": r.qty,
            "auto": bool(r.auto),
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in reqs],
        "can_edit": user.role in tuple(roles.INVENTORY_ACCESS),
    }


@app.post("/api/consumables")
def create_consumable(
    payload: schemas.ConsumableCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    if payload.kind not in roles.CONSUMABLE_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri mahsulot turi")
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    data["unit"] = data.get("unit") or roles.CONSUMABLE_UNITS.get(data["kind"], "dona")
    c = models.Consumable(**data)
    db.add(c); db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit()
    return _consumable_out(db, c)


@app.put("/api/consumables/{cid}")
def update_consumable(
    cid: int,
    payload: schemas.ConsumableUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    fields = payload.model_dump(exclude_unset=True)
    # Qoldiq qo'lda o'zgartirilmaydi - faqat harakat orqali.
    fields.pop("qty", None)
    for k, v in fields.items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit()
    return _consumable_out(db, c)


@app.delete("/api/consumables/{cid}")
def delete_consumable(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    db.query(models.StockMove).filter(
        models.StockMove.consumable_id == cid).delete()
    db.query(models.PurchaseRequest).filter(
        models.PurchaseRequest.consumable_id == cid).delete()
    db.delete(c); db.commit()
    return {"ok": True}


@app.post("/api/consumables/{cid}/move")
def move_stock(
    cid: int,
    payload: schemas.StockMoveCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    """Kirim/chiqim. Qoldiq faqat shu yerdan o'zgaradi - shunda
    "marker qayoqqa ketdi" savoli javobsiz qolmaydi."""
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    if payload.reason not in roles.STOCK_MOVE_LABELS:
        raise HTTPException(400, "Noto'g'ri sabab")
    if not payload.qty:
        raise HTTPException(400, "Miqdorni kiriting")

    delta = abs(payload.qty) if payload.reason == "in" else -abs(payload.qty)
    if payload.reason == "correction":
        delta = payload.qty
    if c.qty + delta < 0:
        raise HTTPException(
            400, f"Omborda {c.qty} {c.unit or 'dona'} bor — "
                 f"{abs(delta)} chiqarib bo'lmaydi")

    db.add(models.StockMove(
        consumable_id=cid, delta=delta, reason=payload.reason,
        note=payload.note, created_by=user.full_name))
    c.qty = (c.qty or 0) + delta
    db.commit(); db.refresh(c)
    _check_stock(db, c); db.commit(); db.refresh(c)
    return _consumable_out(db, c)


@app.get("/api/consumables/{cid}/moves")
def list_moves(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_VIEW)),
):
    rows = (db.query(models.StockMove)
            .filter(models.StockMove.consumable_id == cid)
            .order_by(models.StockMove.created_at.desc()).limit(100).all())
    return [{
        "id": m.id, "delta": m.delta, "reason": m.reason,
        "reason_label": roles.STOCK_MOVE_LABELS.get(m.reason, m.reason),
        "note": m.note, "by": m.created_by,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in rows]


@app.post("/api/purchase-requests/{rid}/close")
def close_request(
    rid: int,
    payload: schemas.PurchaseClose,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.INVENTORY_ACCESS)),
):
    """Xarid so'rovini yopish. "received" bo'lsa qoldiq ham to'ldiriladi."""
    pr = db.query(models.PurchaseRequest).get(rid)
    if not pr:
        raise HTTPException(404, "So'rov topilmadi")
    c = db.query(models.Consumable).get(pr.consumable_id)
    if payload.status == "done" and c:
        qty = payload.qty or pr.qty
        db.add(models.StockMove(
            consumable_id=c.id, delta=abs(qty), reason="in",
            note=f"Xarid so'rovi #{pr.id}", created_by=user.full_name))
        c.qty = (c.qty or 0) + abs(qty)
    pr.status = payload.status
    pr.closed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "qty": c.qty if c else None}


# =====================================================================
#  USTOZ ISH HAQI  —  yoqlamadan avtomat
#
#  Hech kim hech narsani bosmaydi. Ustoz yoqlama qo'yishi bilan
#  oyligi o'sadi. Yoqlama yo'q — oylik ham yo'q.
#
#  Ishlab topilgan pul hech qayerda saqlanmaydi — har safar darslardan
#  qayta hisoblanadi. Saqlanadigan yagona narsa — QO'LDAN CHIQQAN pul
#  (TeacherPayment). Balans = ishlab topgan − berilgan.
# =====================================================================
def _teacher_earned(db: Session, teacher_id: int, *,
                    since: date = None, until: date = None) -> dict:
    """Ustozning berilgan davrda ishlab topgan puli.

    until berilmasa — BUGUNGACHA. Ya'ni ustoz oy o'rtasida kirsa,
    "shu kungacha ishlab topganim" ni ko'radi."""
    until = until or date.today()
    q = (db.query(models.Lesson)
         .filter(models.Lesson.teacher_id == teacher_id,
                 models.Lesson.held == 1,
                 models.Lesson.date <= until))
    if since:
        q = q.filter(models.Lesson.date >= since)
    lessons = q.order_by(models.Lesson.date).all()

    groups = {g.id: g for g in db.query(models.Group).all()}
    rates = billing.grade_rates(db)
    total = 0.0
    attendances = 0
    by_group: dict[int, dict] = {}
    by_period: dict[str, dict] = {}

    for l in lessons:
        g = groups.get(l.group_id)
        if not g:
            continue
        # Stavka dars SANASIGA qarab olinadi: ustoz keyin ko'tarilgan
        # bo'lsa ham o'tgan oyning darslari eski narxda qoladi.
        rate, per_student = billing.lesson_rate(db, g, l, rates)
        n = billing.lesson_student_count(db, l)
        amount = n * rate
        total += amount
        attendances += n

        gr = by_group.setdefault(l.group_id, {
            "group_id": l.group_id, "group": g.name,
            "rate_per_student_month": per_student,
            "standard_lessons": g.standard_lessons_per_month or 12,
            "rate": rate, "lessons": 0, "attendances": 0, "amount": 0.0,
        })
        gr["lessons"] += 1
        gr["attendances"] += n
        gr["amount"] += amount
        gr["rate"] = rate
        gr["rate_per_student_month"] = per_student

        per = l.date.isoformat()[:7]
        pr = by_period.setdefault(per, {
            "period": per, "lessons": 0, "attendances": 0, "amount": 0.0,
        })
        pr["lessons"] += 1
        pr["attendances"] += n
        pr["amount"] += amount

    return {
        "amount": round(total, 2),
        "attendances": attendances,
        "lessons": len(lessons),
        "by_group": sorted(by_group.values(), key=lambda r: -r["amount"]),
        "by_period": sorted(by_period.values(), key=lambda r: r["period"]),
    }


# =====================================================================
#  USTOZ KARYERA XARITASI
#
#  Junior -> Middle -> Senior -> Expert -> Head -> Metodist.
#  Har bir darajaning o'z narxi, o'z guruh soni va o'z o'tish sharti
#  bor. Tizim mezonlarni o'zi hisoblaydi va darajani o'zi o'zgartiradi
#  — lekin har bir o'zgarish tarixga sababi bilan yoziladi va
#  asoschiga vazifa bo'lib boradi, ya'ni jimgina bo'lmaydi.
# =====================================================================
def _grade_rows(db: Session) -> list:
    return (db.query(models.TeacherGrade)
            .order_by(models.TeacherGrade.order_no).all())


def _grade_map(db: Session) -> dict:
    return {g.key: g for g in db.query(models.TeacherGrade).all()}


def _grade_after(db: Session, key: str) -> models.TeacherGrade | None:
    rows = _grade_rows(db)
    keys = [g.key for g in rows]
    if key not in keys:
        return rows[0] if rows else None
    i = keys.index(key)
    return rows[i + 1] if i + 1 < len(rows) else None


def _teacher_months(t: models.Teacher, today: date) -> float:
    """Umumiy tajriba (oy): ustozlik + undan oldingi support/volontyor."""
    base = float(t.support_months or 0)
    if t.hired_date:
        days = (today - t.hired_date).days
        base += max(0.0, days / 30.4)
    return round(base, 1)


def _teacher_age(t: models.Teacher, today: date) -> int | None:
    if not t.birth_date:
        return None
    y = today.year - t.birth_date.year
    if (today.month, today.day) < (t.birth_date.month, t.birth_date.day):
        y -= 1
    return y


def _teacher_exam_results(db: Session, teacher_id: int, *,
                          since: date, kinds: list[str] | None = None) -> list:
    """Ustozning guruhlaridagi imtihon natijalari. Kelmagan o'quvchi
    hisobga olinmaydi — u bilmagani uchun emas, kelmagani uchun 0."""
    gids = [g.id for g in db.query(models.Group)
            .filter(models.Group.teacher_id == teacher_id).all()]
    if not gids:
        return []
    q = (db.query(models.Exam)
         .filter(models.Exam.group_id.in_(gids), models.Exam.date >= since))
    if kinds:
        q = q.filter(models.Exam.kind.in_(kinds))
    exams = q.all()
    if not exams:
        return []
    rows = (db.query(models.ExamResult)
            .filter(models.ExamResult.exam_id.in_([e.id for e in exams]))
            .all())
    return [(e, r) for e in exams for r in rows
            if r.exam_id == e.id and not r.absent and r.percent is not None]


def _teacher_pass_rate(db: Session, t: models.Teacher,
                       pass_mark: float, today: date) -> dict:
    """Necha foiz o'quvchi bosqichdan MUVAFFAQIYATLI o'tdi.

    O'lchov — kurs yakuni (end of course) testi: aynan shu test
    o'quvchining keyingi bosqichga tayyorligini ko'rsatadi."""
    since = today - timedelta(days=30 * roles.PASS_WINDOW_MONTHS)
    rows = _teacher_exam_results(db, t.id, since=since, kinds=["end", "mid"])
    if not rows:
        return {"rate": None, "results": 0, "exams": 0, "passed": 0}
    passed = sum(1 for _e, r in rows if (r.percent or 0) >= pass_mark)
    exams = len({e.id for e, _r in rows})
    return {
        "rate": round(passed / len(rows) * 100, 1),
        "results": len(rows), "exams": exams, "passed": passed,
    }


def _teacher_test_avg(db: Session, t: models.Teacher, today: date) -> dict:
    """Oylik test o'rtachasi — barcha test turlari bo'yicha."""
    since = today - timedelta(days=roles.TEST_WINDOW_DAYS)
    rows = _teacher_exam_results(db, t.id, since=since)
    if not rows:
        return {"avg": None, "results": 0, "exams": 0}
    vals = [r.percent or 0 for _e, r in rows]
    return {
        "avg": round(sum(vals) / len(vals), 1),
        "results": len(vals),
        "exams": len({e.id for e, _r in rows}),
    }


def _teacher_high_results(db: Session, t: models.Teacher,
                          band: float) -> int:
    """Nechta o'quvchisi yuqori natija (mock band) oldi. Head va
    Metodist darajasi uchun shart."""
    if not band:
        return 0
    gids = [g.id for g in db.query(models.Group)
            .filter(models.Group.teacher_id == t.id).all()]
    if not gids:
        return 0
    exams = (db.query(models.Exam)
             .filter(models.Exam.group_id.in_(gids),
                     models.Exam.kind == "mock").all())
    if not exams:
        return 0
    rows = (db.query(models.ExamResult)
            .filter(models.ExamResult.exam_id.in_([e.id for e in exams]),
                    models.ExamResult.band.isnot(None)).all())
    # Bir o'quvchi bir necha mock topshirgan bo'lishi mumkin — eng
    # yaxshisi olinadi, aks holda bitta odam ro'yxatni to'ldirib
    # yuborardi.
    best: dict[int, float] = {}
    for r in rows:
        cur = best.get(r.student_id)
        if cur is None or (r.band or 0) > cur:
            best[r.student_id] = r.band or 0
    return sum(1 for v in best.values() if v >= band)


def _study_items(db: Session, t: models.Teacher, stage: str) -> list:
    """O'qish rejasi. Birinchi so'raganda o'zi yaratiladi."""
    rows = (db.query(models.TeacherStudyItem)
            .filter(models.TeacherStudyItem.teacher_id == t.id,
                    models.TeacherStudyItem.stage == stage).all())
    want = None
    for key, _lbl, books, casts in roles.STUDY_STAGES:
        if key == stage:
            want = [("book", b) for b in books] + \
                   [("podcast", p) for p in casts]
    if want is None:
        return rows
    have = {(r.kind, r.title) for r in rows}
    added = False
    for kind, title in want:
        if (kind, title) in have:
            continue
        db.add(models.TeacherStudyItem(teacher_id=t.id, stage=stage,
                                       kind=kind, title=title, done=0))
        added = True
    if added:
        db.commit()
        rows = (db.query(models.TeacherStudyItem)
                .filter(models.TeacherStudyItem.teacher_id == t.id,
                        models.TeacherStudyItem.stage == stage).all())
    return rows


def _study_progress(db: Session, t: models.Teacher, stage: str) -> dict:
    rows = _study_items(db, t, stage)
    done = sum(1 for r in rows if r.done)
    return {"done": done, "total": len(rows),
            "ok": bool(rows) and done == len(rows)}


def _grade_state(db: Session, t: models.Teacher,
                 today: date | None = None) -> dict:
    """Ustozning hozirgi holati va keyingi darajaga nima yetishmayotgani.

    Bu funksiya hech narsani o'zgartirmaydi — faqat hisoblaydi."""
    today = today or date.today()
    gm = _grade_map(db)
    cur_key = t.grade or roles.FIRST_GRADE
    cur = gm.get(cur_key)
    nxt = _grade_after(db, cur_key)

    months = _teacher_months(t, today)
    age = _teacher_age(t, today)
    pass_mark = (cur.level_pass_percent if cur else None) \
        or roles.LEVEL_PASS_PERCENT
    passing = _teacher_pass_rate(db, t, pass_mark, today)
    testing = _teacher_test_avg(db, t, today)
    group_count = (db.query(models.Group)
                   .filter(models.Group.teacher_id == t.id).count())

    enough = (testing["results"] >= roles.GRADE_MIN_RESULTS
              and testing["exams"] >= roles.GRADE_MIN_EXAMS)
    enough_pass = (passing["results"] >= roles.GRADE_MIN_RESULTS
                   and passing["exams"] >= roles.GRADE_MIN_EXAMS)

    # ---- Keyingi darajaga nima yetishmayapti ----
    missing = []
    ready = False
    if nxt:
        need_rate = cur.promote_pass_rate if cur else None
        if need_rate is not None:
            if not enough_pass:
                missing.append({
                    "key": "data",
                    "text": (f"Yetarli natija yo'q — kamida "
                             f"{roles.GRADE_MIN_RESULTS} ta natija va "
                             f"{roles.GRADE_MIN_EXAMS} ta test kerak "
                             f"(hozir {passing['results']} / "
                             f"{passing['exams']})")})
            elif (passing["rate"] or 0) < need_rate:
                missing.append({
                    "key": "pass_rate",
                    "text": (f"O'quvchilarning {need_rate}% i bosqichdan "
                             f"o'tishi kerak — hozir "
                             f"{passing['rate']}%")})
        if months < (nxt.min_months or 0):
            missing.append({
                "key": "months",
                "text": (f"Tajriba {nxt.min_months} oy bo'lishi kerak — "
                         f"hozir {round(months)} oy")})
        if nxt.cert_min and (t.cert_score or 0) < nxt.cert_min:
            missing.append({
                "key": "cert",
                "text": (f"Sertifikat: {nxt.cert_label} — hozir "
                         f"{t.cert or 'yo’q'}")})
        if nxt.min_age and (age is None or age < nxt.min_age):
            missing.append({
                "key": "age",
                "text": (f"Yoshi {nxt.min_age}+ bo'lishi kerak — "
                         + (f"hozir {age}" if age is not None
                            else "tug'ilgan sana kiritilmagan"))})
        if nxt.min_skill and (t.skill_score or 0) < nxt.min_skill:
            missing.append({
                "key": "skill",
                "text": (f"Dars berish mahorati {round(nxt.min_skill)}+ "
                         f"ball — hozir {t.skill_score or 0}")})
        if nxt.needs_qualification and not t.qualification:
            missing.append({
                "key": "qualification",
                "text": ("Metodika sertifikati kerak: "
                         + " / ".join(roles.METODIST_QUALIFICATIONS))})
        if nxt.min_results:
            have = _teacher_high_results(db, t, nxt.result_band or 0)
            if have < nxt.min_results:
                missing.append({
                    "key": "results",
                    "text": (f"{nxt.min_results} ta o'quvchi IELTS "
                             f"{nxt.result_band}+ olishi kerak — "
                             f"hozir {have} ta")})
        stage = roles.STUDY_REQUIRED_FOR.get(nxt.key)
        if stage:
            sp = _study_progress(db, t, stage)
            if not sp["ok"]:
                missing.append({
                    "key": "study",
                    "text": (f"O'qish rejasi tugallanmagan — "
                             f"{sp['done']}/{sp['total']} "
                             f"kitob va podkast")})
        ready = not missing

    # ---- Pastga tushish ----
    floor = cur.demote_below if cur else None
    should_demote = bool(
        floor is not None and cur and cur.demote_to and enough
        and testing["avg"] is not None and testing["avg"] < floor)

    # ---- Qayta tayyorlash (50% dan past) ----
    need_remediation = bool(
        enough_pass and passing["rate"] is not None
        and passing["rate"] < roles.REMEDIATION_BELOW)
    in_remediation = bool(t.remediation_until
                          and t.remediation_until >= today)

    max_groups = t.max_groups or (cur.max_groups if cur else None) \
        or roles.TEACHER_MAX_GROUPS

    return {
        "teacher_id": t.id,
        "full_name": t.full_name,
        "branch": t.branch.name if t.branch else None,
        "grade": cur_key,
        "grade_label": (cur.label if cur
                        else roles.GRADE_LABELS.get(cur_key, cur_key)),
        "tone": roles.GRADE_TONES.get(cur_key, "slate"),
        "grade_since": t.grade_since.isoformat() if t.grade_since else None,
        "rate_per_student": cur.rate_per_student if cur else 0,
        "next_grade": nxt.key if nxt else None,
        "next_label": nxt.label if nxt else None,
        "next_rate": nxt.rate_per_student if nxt else None,
        "months": round(months, 1),
        "age": age,
        "cert": t.cert,
        "cert_score": t.cert_score,
        "qualification": t.qualification,
        "skill_score": t.skill_score,
        "groups": group_count,
        "min_groups": cur.min_groups if cur else None,
        "max_groups": max_groups,
        "pass_rate": passing["rate"],
        "pass_results": passing["results"],
        "pass_needed": cur.promote_pass_rate if cur else None,
        "pass_mark": pass_mark,
        "test_avg": testing["avg"],
        "test_results": testing["results"],
        "demote_below": floor,
        "enough_data": enough,
        "ready": ready,
        "missing": missing,
        "should_demote": should_demote,
        "need_remediation": need_remediation,
        "in_remediation": in_remediation,
        "remediation_until": (t.remediation_until.isoformat()
                              if t.remediation_until else None),
        "remediation_reason": t.remediation_reason,
    }


def _sync_group_rates(db: Session, t: models.Teacher, rate: float) -> int:
    """Darajaning narxini ustozning guruhlariga qo'yadi. Qo'lda narx
    kiritilgan guruhga TEGILMAYDI — istisno holat shunday saqlanadi."""
    n = 0
    for g in (db.query(models.Group)
              .filter(models.Group.teacher_id == t.id).all()):
        if g.rate_manual:
            continue
        if (g.teacher_rate_per_student or 0) != rate:
            g.teacher_rate_per_student = rate
            n += 1
    return n


def _set_grade(db: Session, t: models.Teacher, to_key: str, *,
               kind: str, reason: str, by: str = "Tizim",
               pass_rate: float | None = None,
               test_avg: float | None = None,
               on: date | None = None) -> models.TeacherGradeEvent:
    """Darajani o'zgartiradi va TARIXGA yozadi.

    Tarix shunchaki jurnal emas: oylik ham shundan hisoblanadi, ya'ni
    o'tgan oyning darslari eski stavkada qolaveradi."""
    on = on or date.today()
    gm = _grade_map(db)
    before = gm.get(t.grade or "")
    after = gm.get(to_key)

    ev = models.TeacherGradeEvent(
        teacher_id=t.id, from_grade=t.grade, to_grade=to_key, kind=kind,
        effective_from=on, reason=reason, pass_rate=pass_rate,
        test_avg=test_avg,
        rate_before=before.rate_per_student if before else None,
        rate_after=after.rate_per_student if after else None,
        decided_by=by)
    db.add(ev)

    t.grade = to_key
    t.grade_since = on
    if after:
        _sync_group_rates(db, t, after.rate_per_student or 0)
    return ev


def _career_task(db: Session, t: models.Teacher, *, title: str,
                 body: str, priority: str = "normal") -> None:
    """Daraja o'zgargani jimgina o'tib ketmasin — vazifa bo'lib
    ko'rinadi."""
    if db.query(models.Task).filter(models.Task.title == title).first():
        return
    who = (db.query(models.User)
           .filter(models.User.role == roles.ACADEMIC_HEAD,
                   models.User.is_active == 1).first()) or \
          _hr_user(db, t.branch_id)
    task = models.Task(
        title=title, description=body,
        assignee_id=who.id if who else None,
        branch_id=t.branch_id,
        deadline=date.today() + timedelta(days=3),
        priority=priority, source="manual", created_by="Tizim")
    db.add(task)
    db.flush()
    _ensure_public_id(db, "task", task)


_GRADE_RUN_AT: list = [None]


def _apply_grade_rules_throttled(db: Session, minutes: int = 30) -> dict:
    """Har bir so'rovda emas, yarim soatda bir marta. Karyera bo'limi
    ochilganda esa darrov ishlaydi (_apply_grade_rules to'g'ridan-
    to'g'ri chaqiriladi)."""
    now = datetime.utcnow()
    last = _GRADE_RUN_AT[0]
    if last and (now - last).total_seconds() < minutes * 60:
        return {}
    _GRADE_RUN_AT[0] = now
    try:
        return _apply_grade_rules(db)
    except Exception:
        db.rollback()
        return {}


def _apply_grade_rules(db: Session) -> dict:
    """AVTOMAT: mezonlar bajarilgan bo'lsa darajani ko'taradi, oylik
    test o'rtachasi pasaygan bo'lsa tushiradi, natija 50% dan past
    bo'lsa qayta tayyorlashga qo'yadi.

    Hech kim tugma bosmaydi. Lekin har bir o'zgarish tarixga sababi
    va raqamlari bilan yoziladi hamda vazifa bo'lib chiqadi — kerak
    bo'lsa asoschi orqaga qaytara oladi."""
    today = date.today()
    out = {"promoted": 0, "demoted": 0, "remediation": 0, "cleared": 0}
    teachers = (db.query(models.Teacher)
                .filter(models.Teacher.is_active == 1).all())
    if not teachers or not _grade_rows(db):
        return out

    for t in teachers:
        try:
            st = _grade_state(db, t, today)
        except Exception:
            continue

        # --- Qayta tayyorlash muddati tugadimi ---
        if t.remediation_until and t.remediation_until < today:
            t.remediation_until = None
            t.remediation_reason = None
            db.add(models.TeacherGradeEvent(
                teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
                kind="remediation_done", effective_from=today,
                reason="Qayta tayyorlash muddati tugadi",
                decided_by="Tizim"))
            out["cleared"] += 1

        # --- Natija 50% dan past: yangi guruh yo'q, qayta test ---
        if st["need_remediation"] and not st["in_remediation"]:
            until = today + timedelta(days=roles.REMEDIATION_DAYS)
            t.remediation_until = until
            t.remediation_reason = (
                f"O'quvchilarning atigi {st['pass_rate']}% i bosqichdan "
                f"o'tdi ({roles.REMEDIATION_BELOW}% dan past)")
            db.add(models.TeacherGradeEvent(
                teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
                kind="remediation", effective_from=today,
                reason=t.remediation_reason,
                pass_rate=st["pass_rate"], decided_by="Tizim"))
            _career_task(
                db, t, priority="high",
                title=(f"Qayta tayyorlash: {t.full_name} — "
                       f"{until.isoformat()}"),
                body=(f"O'quvchilarning {st['pass_rate']}% i bosqichdan "
                      f"o'tdi ({st['pass_results']} ta natija bo'yicha).\n\n"
                      "Hujjat bo'yicha tartib:\n"
                      "1. O'tgan o'quvchilar boshqa ustozga beriladi.\n"
                      "2. O'ta olmaganlarini ustozning o'zi qayta "
                      "tayyorlaydi.\n"
                      f"3. {until.isoformat()} da qayta test.\n"
                      "4. Shundan keyingina yangi guruh ochiladi.\n\n"
                      "Shu muddatgacha tizim bu ustozga yangi guruh "
                      "biriktirishga yo'l qo'ymaydi."))
            out["remediation"] += 1
            continue      # tushirish bilan bir vaqtda bo'lmasin

        # --- Pastga tushirish ---
        if st["should_demote"]:
            gm = _grade_map(db)
            cur = gm.get(t.grade or "")
            to_key = cur.demote_to if cur else None
            if to_key and to_key in gm:
                reason = (f"Oylik test o'rtachasi {st['test_avg']}% — "
                          f"{st['demote_below']}% dan past "
                          f"({st['test_results']} ta natija)")
                _set_grade(db, t, to_key, kind="demote", reason=reason,
                           test_avg=st["test_avg"])
                _career_task(
                    db, t, priority="high",
                    title=(f"Daraja tushdi: {t.full_name} — "
                           f"{gm[to_key].label} ({today.isoformat()})"),
                    body=(f"{reason}\n\n"
                          f"Yangi stavka: {gm[to_key].rate_per_student:,.0f} "
                          "so'm (bir o'quvchidan).\n"
                          "O'tgan oylarning oyligi o'zgarmaydi — eski "
                          "stavkada qoladi.\n\n"
                          "Xato bo'lsa Karyera bo'limidan darajani "
                          "qaytarish mumkin.").replace(",", " "))
                out["demoted"] += 1
                continue

        # --- Ko'tarish ---
        if st["ready"] and st["next_grade"] and not st["in_remediation"]:
            gm = _grade_map(db)
            to_key = st["next_grade"]
            reason = (f"Barcha shartlar bajarildi: o'quvchilarning "
                      f"{st['pass_rate']}% i bosqichdan o'tdi, tajriba "
                      f"{round(st['months'])} oy, sertifikat "
                      f"{t.cert or '—'}")
            _set_grade(db, t, to_key, kind="promote", reason=reason,
                       pass_rate=st["pass_rate"], test_avg=st["test_avg"])
            _career_task(
                db, t,
                title=(f"Daraja ko'tarildi: {t.full_name} — "
                       f"{gm[to_key].label} ({today.isoformat()})"),
                body=(f"{reason}\n\n"
                      f"Yangi stavka: {gm[to_key].rate_per_student:,.0f} "
                      "so'm (bir o'quvchidan).\n"
                      f"Endi {gm[to_key].min_groups}-"
                      f"{gm[to_key].max_groups} ta guruh olib bora "
                      "oladi.\n\n"
                      "Ustozni tabriklashni unutmang.").replace(",", " "))
            out["promoted"] += 1

    db.commit()
    return out


def _teacher_paid(db: Session, teacher_id: int, *,
                  since: date = None, until: date = None) -> float:
    q = db.query(models.TeacherPayment).filter(
        models.TeacherPayment.teacher_id == teacher_id)
    if since:
        q = q.filter(models.TeacherPayment.paid_on >= since)
    if until:
        q = q.filter(models.TeacherPayment.paid_on <= until)
    return round(sum(p.amount or 0 for p in q.all()), 2)


def _teacher_of_user(db: Session, user: models.User) -> models.Teacher | None:
    """Foydalanuvchi hisobiga bog'langan ustoz yozuvi. Ism bo'yicha
    topiladi — ustozlar ro'yxati va xodimlar ro'yxati alohida."""
    return (db.query(models.Teacher)
            .filter(models.Teacher.full_name == user.full_name).first())


def _salary_card(db: Session, t: models.Teacher) -> dict:
    """Ustozning ish haqi kartasi: ishlab topgan, olgan, balans."""
    today = date.today()
    m_start, _m_end = billing.month_bounds(today.year, today.month)

    all_time = _teacher_earned(db, t.id)
    this_month = _teacher_earned(db, t.id, since=m_start)
    paid_all = _teacher_paid(db, t.id)
    paid_month = _teacher_paid(db, t.id, since=m_start)

    balance = round(all_time["amount"] - paid_all, 2)

    pays = (db.query(models.TeacherPayment)
            .filter(models.TeacherPayment.teacher_id == t.id)
            .order_by(models.TeacherPayment.paid_on.desc()).limit(50).all())

    # O'tgan oylardan qolgan farq: bu oyning boshigacha bo'lgan balans
    prev_earned = _teacher_earned(db, t.id, until=m_start - timedelta(days=1))
    prev_paid = _teacher_paid(db, t.id, until=m_start - timedelta(days=1))
    carry = round(prev_earned["amount"] - prev_paid, 2)

    return {
        "teacher_id": t.id,
        "full_name": t.full_name,
        "branch": t.branch.name if t.branch else None,
        # Shu oy
        "month": today.isoformat()[:7],
        "earned_month": this_month["amount"],
        "paid_month": paid_month,
        "lessons_month": this_month["lessons"],
        "attendances_month": this_month["attendances"],
        # Umumiy balans
        "earned_total": all_time["amount"],
        "paid_total": paid_all,
        "balance": balance,
        # O'tgan oylardan kelgan farq: musbat - biz qarzdormiz,
        # manfiy - ustoz ortiqcha olgan
        "carry": carry,
        "carry_label": (
            "O'tgan oylardan qarzimiz" if carry > 0
            else "O'tgan oyda ortiqcha berilgan" if carry < 0
            else "O'tgan oylar yopilgan"),
        # Avans chegarasi: ishlab topganidan ortiq berilmaydi
        "advance_available": max(0.0, balance),
        "by_group": this_month["by_group"],
        "by_period": all_time["by_period"][-12:],
        "payments": [{
            "id": p.id, "amount": p.amount, "kind": p.kind,
            "kind_label": roles.TEACHER_PAYMENT_LABELS.get(p.kind, p.kind),
            "date": p.paid_on.isoformat() if p.paid_on else None,
            "period": p.period, "note": p.note, "by": p.created_by,
        } for p in pays],
    }


@app.get("/api/teachers/{teacher_id}/salary")
def teacher_salary(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_SELF_VIEW)),
):
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    # Ustoz faqat o'zining oyligini ko'radi
    if user.role in (roles.TEACHER, roles.SUPPORT_TEACHER):
        me = _teacher_of_user(db, user)
        if not me or me.id != teacher_id:
            raise HTTPException(403, "Faqat o'z oyligingizni ko'ra olasiz")
    card = _salary_card(db, t)
    card["can_pay"] = user.role in tuple(roles.SALARY_PAY)
    return card


@app.get("/api/my/salary")
def my_salary(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_SELF_VIEW)),
):
    """Ustozning o'z oyligi. Kirgan zahoti shu kungacha ishlab topgan
    puli va balansi ko'rinadi."""
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Sizga bog'langan ustoz yozuvi topilmadi")
    card = _salary_card(db, t)
    card["can_pay"] = False
    return card


@app.get("/api/payroll")
def payroll_overview(
    year: int | None = None,
    month: int | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS, *roles.SALARY_VIEW_ALL)),
):
    """Barcha ustozlar bo'yicha oylik. Hech narsa "ishga tushirilmaydi" —
    ro'yxat har safar darslardan qayta hisoblanadi."""
    # Daraja o'zgarishi oylikka ta'sir qiladi - avval qoidalarni
    # yurgizamiz, keyin hisoblaymiz.
    _apply_grade_rules_throttled(db)
    today = date.today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)
    period = f"{y:04d}-{m:02d}"

    q = scope_to_branch(db.query(models.Teacher), models.Teacher, user, branch_id)
    teachers = q.filter(models.Teacher.is_active == 1).all()

    rows = []
    for t in teachers:
        e = _teacher_earned(db, t.id, since=start, until=end)
        paid = _teacher_paid(db, t.id, since=start, until=end)
        card_balance = round(_teacher_earned(db, t.id)["amount"]
                             - _teacher_paid(db, t.id), 2)
        if e["amount"] == 0 and paid == 0:
            continue
        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "lessons": e["lessons"],
            "attendances": e["attendances"],
            "earned": e["amount"],
            "paid": paid,
            "left": round(e["amount"] - paid, 2),
            "balance": card_balance,
            "groups": e["by_group"],
        })
    rows.sort(key=lambda r: -r["earned"])
    return {
        "period": period,
        "rows": rows,
        "teacher_count": len(rows),
        "earned": round(sum(r["earned"] for r in rows), 2),
        "paid": round(sum(r["paid"] for r in rows), 2),
        "left": round(sum(r["left"] for r in rows), 2),
        "kinds": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.TEACHER_PAYMENT_KINDS],
        "can_pay": user.role in tuple(roles.SALARY_PAY),
    }


@app.post("/api/teachers/{teacher_id}/payments")
def pay_teacher(
    teacher_id: int,
    payload: schemas.TeacherPaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_PAY)),
):
    """Ustozga pul berish. Avans ishlab topilgan puldan oshmaydi —
    aks holda ustoz ketib qolsa pul qaytmaydi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if payload.kind not in roles.TEACHER_PAYMENT_LABELS:
        raise HTTPException(400, "Noto'g'ri to'lov turi")
    if not payload.amount or payload.amount <= 0:
        raise HTTPException(400, "Summani kiriting")

    earned = _teacher_earned(db, t.id)["amount"]
    paid = _teacher_paid(db, t.id)
    available = earned - paid
    if payload.kind == "advance" and payload.amount > available:
        raise HTTPException(
            400,
            f"Avans ishlab topilgan puldan ko'p bo'lmasligi kerak. "
            f"Hozirgacha ishlab topgani {earned:,.0f} so'm, olgani "
            f"{paid:,.0f} so'm — bera oladigan summa "
            f"{max(0, available):,.0f} so'm.".replace(",", " "))

    p = models.TeacherPayment(
        teacher_id=t.id, amount=payload.amount, kind=payload.kind,
        period=payload.period or date.today().isoformat()[:7],
        paid_on=payload.date or date.today(),
        method=payload.method, note=payload.note,
        created_by=user.full_name)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="teacher", action="salary_change",
              entity_id=t.id, entity_label=t.full_name,
              branch_id=t.branch_id,
              field=roles.TEACHER_PAYMENT_LABELS[payload.kind],
              new_value=f"{payload.amount:,.0f}".replace(",", " "))
    db.commit()
    return _salary_card(db, t)


@app.delete("/api/teacher-payments/{payment_id}")
def delete_teacher_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_PAY)),
):
    p = db.query(models.TeacherPayment).get(payment_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    t = db.query(models.Teacher).get(p.teacher_id)
    audit.log(db, user, entity="teacher", action="delete", entity_id=p.teacher_id,
              entity_label=t.full_name if t else "—",
              field="Ustoz to'lovi",
              old_value=f"{p.amount:,.0f}".replace(",", " "))
    db.delete(p); db.commit()
    return {"ok": True}


# =====================================================================
#  QARZDORLAR BILAN ISHLASH
#  Administrator uchun ish maydoni: kimga qo'ng'iroq qilish kerak,
#  kim qachonga va'da bergan, kim va'dasini buzgan.
# =====================================================================
def _last_charge_date(db: Session, student_id: int) -> date | None:
    row = (db.query(models.Payment)
           .filter(models.Payment.student_id == student_id,
                   models.Payment.kind == "charge")
           .order_by(models.Payment.created_at.desc()).first())
    return row.created_at.date() if row and row.created_at else None


@app.get("/api/debtors")
def list_debtors(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    """Qarzdorlar ro'yxati. Eng shoshilinchi tepada: va'dasi o'tib
    ketganlar, keyin eski qarzlar."""
    today = date.today()
    q = scope_to_branch(db.query(models.Student), models.Student, user, branch_id)
    students = q.filter(models.Student.status.in_(["active", "trial", "frozen"])).all()

    # Oxirgi bog'lanish yozuvlari
    contacts: dict[int, models.DebtorContact] = {}
    for c in (db.query(models.DebtorContact)
              .order_by(models.DebtorContact.contacted_on).all()):
        contacts[c.student_id] = c

    rows = []
    for s in students:
        bal = student_balance(db, s.id)
        if bal >= 0:
            continue
        debt = abs(bal)
        since = _last_charge_date(db, s.id) or s.enrolled_date or today
        days = (today - since).days
        key, label, tone = roles.debt_urgency(days)

        c = contacts.get(s.id)
        promised = c.promised_date if c else None
        broken = bool(promised and promised < today)

        rows.append({
            "student_id": s.id,
            "public_id": s.public_id,
            "full_name": s.full_name,
            "phone": s.phone,
            "parent_phone": s.parent_phone,
            "group_id": s.group_id,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "status": s.status,
            "debt": round(debt, 2),
            "days": days,
            "urgency": key,
            "urgency_label": label,
            "urgency_tone": tone,
            "last_contact": c.contacted_on.isoformat() if c else None,
            "last_result": c.result if c else None,
            "last_result_label": (roles.DEBT_CONTACT_LABELS.get(c.result, c.result)
                                  if c else None),
            "last_note": c.note if c else None,
            "promised_date": promised.isoformat() if promised else None,
            "promised_amount": c.promised_amount if c else None,
            # Va'dasini buzgan - eng birinchi shunga qo'ng'iroq qilinadi
            "promise_broken": broken,
            "days_since_contact": ((today - c.contacted_on).days
                                   if c and c.contacted_on else None),
        })

    # Tartib: va'dasi buzilgan → bugun va'da qilgan → hech bog'lanilmagan
    # → qarzi kattaroq
    def sort_key(r):
        promise_today = r["promised_date"] == today.isoformat()
        return (
            0 if r["promise_broken"] else 1 if promise_today else
            2 if not r["last_contact"] else 3,
            -r["debt"],
        )
    rows.sort(key=sort_key)

    return {
        "rows": rows,
        "total_debt": round(sum(r["debt"] for r in rows), 2),
        "count": len(rows),
        "broken_promises": sum(1 for r in rows if r["promise_broken"]),
        "due_today": sum(1 for r in rows
                         if r["promised_date"] == today.isoformat()),
        "never_contacted": sum(1 for r in rows if not r["last_contact"]),
        "results": [{"key": k, "label": lbl, "tone": t}
                    for k, lbl, t in roles.DEBT_CONTACT_RESULTS],
    }


@app.post("/api/debtors/contact")
def add_debtor_contact(
    payload: schemas.DebtorContactCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    """"Bog'lanildi" tugmasi. Qachon to'layman deganini yozib qo'yadi —
    ertaga kimga qo'ng'iroq qilish kerakligi shundan chiqadi."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.result not in roles.DEBT_CONTACT_LABELS:
        raise HTTPException(400, "Noto'g'ri natija")
    if payload.result == "promised" and not payload.promised_date:
        raise HTTPException(400, "Qachonga to'layman deganini yozing")

    c = models.DebtorContact(
        student_id=s.id,
        contacted_on=date.today(),
        promised_date=payload.promised_date,
        promised_amount=payload.promised_amount,
        result=payload.result,
        note=payload.note,
        created_by=user.full_name)
    db.add(c); db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Qarz bo'yicha bog'lanildi",
              new_value=roles.DEBT_CONTACT_LABELS[payload.result]
              + (f" — {payload.promised_date}" if payload.promised_date else ""))
    db.commit()
    return {"ok": True}


@app.get("/api/students/{student_id}/debt-contacts")
def student_debt_contacts(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    rows = (db.query(models.DebtorContact)
            .filter(models.DebtorContact.student_id == student_id)
            .order_by(models.DebtorContact.contacted_on.desc()).all())
    return [{
        "id": c.id,
        "date": c.contacted_on.isoformat() if c.contacted_on else None,
        "result": c.result,
        "result_label": roles.DEBT_CONTACT_LABELS.get(c.result, c.result),
        "tone": roles.DEBT_CONTACT_TONE.get(c.result, "slate"),
        "promised_date": c.promised_date.isoformat() if c.promised_date else None,
        "promised_amount": c.promised_amount,
        "note": c.note,
        "by": c.created_by,
    } for c in rows]


# =====================================================================
#  ADMINISTRATOR PANELI
#  Administratorga daromad grafigi kerak emas — unga BUGUN nima
#  qilish kerakligi kerak: qaysi guruhni to'ldirish, kim ketdi,
#  qaysi ustoz o'quvchini ushlab tura olmayapti.
# =====================================================================
@app.get("/api/sales/panel")
def sales_panel(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)

    rooms = {r.id: r for r in db.query(models.Room).all()}
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()

    # --- To'ldirilishi kerak bo'lgan guruhlar ---
    fill_rows = []
    for g in groups:
        n = sum(1 for s in students
                if s.group_id == g.id and s.status in ("active", "trial"))
        cap = _group_capacity(g, rooms)
        if not cap:
            continue
        pct = round(n / cap * 100, 1)
        band, band_label = roles.fill_band(pct)
        if pct >= 85:
            continue          # to'la guruh - ishlash shart emas
        fill_rows.append({
            "group_id": g.id,
            "group": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "", None),
            "level_label": roles.LEVEL_LABELS.get(g.level or "", None),
            "days": [d for d in (g.lesson_days or "").split(",") if d],
            "time": g.lesson_time,
            "students": n,
            "capacity": cap,
            "free": cap - n,
            "fill": pct,
            "band": band,
            "band_label": band_label,
        })
    # Eng ko'p bo'sh joyi bor guruh tepada - eng ko'p pul shu yerda
    fill_rows.sort(key=lambda r: (-r["free"], r["fill"]))

    # --- Shu oy ketganlar ---
    left_rows = []
    for s in students:
        if s.left_date and m_start <= s.left_date <= m_end:
            left_rows.append({
                "student_id": s.id,
                "full_name": s.full_name,
                "group": s.group.name if s.group else None,
                "teacher": (s.group.teacher.full_name
                            if s.group and s.group.teacher else None),
                "left_date": s.left_date.isoformat(),
                "months": (round((s.left_date - s.enrolled_date).days / 30.4, 1)
                           if s.enrolled_date else None),
                "balance": round(student_balance(db, s.id), 2),
            })
    left_rows.sort(key=lambda r: r["left_date"], reverse=True)

    return {
        "month": today.isoformat()[:7],
        "fill": {
            "rows": fill_rows[:20],
            "count": len(fill_rows),
            "free_seats": sum(r["free"] for r in fill_rows),
            # Bo'sh joylar qancha pul turadi
            "lost_income": round(sum(
                r["free"] * next((g.monthly_fee or 0) for g in groups
                                 if g.id == r["group_id"])
                for r in fill_rows), 2),
        },
        "left": {
            "rows": left_rows,
            "count": len(left_rows),
        },
    }


# =====================================================================
#  USTOZLAR REYTINGI
#  Ustoz o'z natijasini va hamkasblari orasidagi o'rnini ko'radi.
#  Boshqa ustozning MAOSHI ko'rinmaydi — faqat natijasi.
# =====================================================================
def _teacher_stats(db: Session, months: int = 12,
                   branch_id: int | None = None,
                   user: models.User | None = None) -> list:
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    tq = db.query(models.Teacher)
    if user is not None:
        tq = scope_to_branch(tq, models.Teacher, user, branch_id)
    elif branch_id:
        tq = tq.filter(models.Teacher.branch_id == branch_id)
    teachers = tq.all()

    groups = db.query(models.Group).all()
    students = db.query(models.Student).all()
    g_by_teacher: dict[int, list] = {}
    for g in groups:
        if g.teacher_id:
            g_by_teacher.setdefault(g.teacher_id, []).append(g)

    # Imtihon natijalari ustoz kesimida
    exam_by_teacher: dict[int, list] = {}
    exams = db.query(models.Exam).all()
    ex_group = {e.id: e.group_id for e in exams if e.date and e.date >= start}
    if ex_group:
        gmap = {g.id: g.teacher_id for g in groups}
        for r in db.query(models.ExamResult).filter(
                models.ExamResult.exam_id.in_(list(ex_group))).all():
            if r.absent or r.percent is None:
                continue
            tid = gmap.get(ex_group.get(r.exam_id))
            if tid:
                exam_by_teacher.setdefault(tid, []).append(r.percent)

    rows = []
    for t in teachers:
        gs = g_by_teacher.get(t.id, [])
        gids = {g.id for g in gs}
        mine = [s for s in students if s.group_id in gids]
        active = [s for s in mine if s.status == "active"]
        left = [s for s in mine if s.left_date and s.left_date >= start]

        # LTV: o'quvchi o'rtacha necha oy qoladi va qancha pul keltiradi
        spans, revenue = [], 0.0
        for s in mine:
            end_d = s.left_date or today
            if s.enrolled_date:
                spans.append(max(0.0, (end_d - s.enrolled_date).days / 30.4))
            revenue += sum(p.amount for p in
                           db.query(models.Payment).filter(
                               models.Payment.student_id == s.id,
                               models.Payment.kind == "payment").all())
        avg_months = round(sum(spans) / len(spans), 1) if spans else 0.0
        ltv = round(revenue / len(mine), 0) if mine else 0.0

        # Retention: qancha o'quvchi qoldi
        base = len(active) + len(left)
        retention = round(len(active) / base * 100, 1) if base else 0.0

        # Dars sifati: imtihon o'rtachasi
        marks = exam_by_teacher.get(t.id, [])
        quality = round(sum(marks) / len(marks), 1) if marks else None

        # Davomat
        att_rows = (db.query(models.Attendance, models.Lesson)
                    .join(models.Lesson,
                          models.Attendance.lesson_id == models.Lesson.id)
                    .filter(models.Lesson.group_id.in_(gids or [-1]),
                            models.Lesson.date >= start).all()) if gids else []
        marked = len(att_rows)
        present = sum(1 for a, _l in att_rows if a.present)
        attendance = round(present / marked * 100, 1) if marked else None

        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "branch_id": t.branch_id,
            "is_active": bool(t.is_active),
            "groups": len(gs),
            "students": len(active),
            "left": len(left),
            "quality": quality,
            "retention": retention,
            "ltv": ltv,
            "avg_months": avg_months,
            "attendance": attendance,
        })

    # Umumiy ball: sifat 40%, retention 30%, LTV 20%, davomat 10%
    max_ltv = max([r["ltv"] for r in rows] or [1]) or 1
    for r in rows:
        parts = {
            "quality": (r["quality"] or 50) if r["quality"] is not None else 50,
            "retention": r["retention"],
            "ltv": min(100.0, r["ltv"] / max_ltv * 100),
            "attendance": (r["attendance"]
                           if r["attendance"] is not None else 50),
        }
        r["parts"] = {k: round(v, 1) for k, v in parts.items()}
        r["score"] = round(sum(
            parts[k] * w / 100
            for k, w in roles.TEACHER_SCORE_DEFAULT.items()), 1)

    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


# ---------------------------------------------------- Karyera xaritasi ----
def _grade_row_out(g: models.TeacherGrade, counts: dict | None = None) -> dict:
    return {
        "key": g.key, "label": g.label, "order_no": g.order_no,
        "rate_per_student": g.rate_per_student or 0,
        "min_months": g.min_months or 0,
        "min_groups": g.min_groups, "max_groups": g.max_groups,
        "cert_label": g.cert_label, "cert_min": g.cert_min,
        "promote_pass_rate": g.promote_pass_rate,
        "demote_below": g.demote_below, "demote_to": g.demote_to,
        "needs_qualification": bool(g.needs_qualification),
        "min_results": g.min_results, "result_band": g.result_band,
        "min_age": g.min_age, "min_skill": g.min_skill,
        "level_pass_percent": g.level_pass_percent,
        "tone": roles.GRADE_TONES.get(g.key, "slate"),
        "teachers": (counts or {}).get(g.key, 0),
    }


@app.get("/api/career")
def career_map(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CAREER_ACCESS)),
):
    """Ustozlarning daraja xaritasi. Ochilgan zahoti avtomat qoidalar
    ham ishlaydi — hech kim tugma bosmaydi."""
    try:
        applied = _apply_grade_rules(db)
    except Exception:
        db.rollback()
        applied = {}

    q = scope_to_branch(db.query(models.Teacher), models.Teacher, user,
                        branch_id)
    teachers = q.filter(models.Teacher.is_active == 1).order_by(
        models.Teacher.full_name).all()

    rows = []
    counts: dict = {}
    for t in teachers:
        st = _grade_state(db, t)
        rows.append(st)
        counts[st["grade"]] = counts.get(st["grade"], 0) + 1

    order = {g: i for i, g in enumerate(roles.GRADE_ORDER)}
    rows.sort(key=lambda r: (-order.get(r["grade"], 0), r["full_name"]))

    return {
        "rows": rows,
        "grades": [_grade_row_out(g, counts) for g in _grade_rows(db)],
        "ready": [r for r in rows if r["ready"]],
        "at_risk": [r for r in rows if r["should_demote"]],
        "remediation": [r for r in rows if r["in_remediation"]],
        "applied": applied,
        "pass_window_months": roles.PASS_WINDOW_MONTHS,
        "test_window_days": roles.TEST_WINDOW_DAYS,
        "min_results": roles.GRADE_MIN_RESULTS,
        "remediation_below": roles.REMEDIATION_BELOW,
        "can_edit": user.role in roles.GRADE_ADMIN,
        "hint": ("Daraja va stavka avtomat o'zgaradi. O'zgargan oyning "
                 "o'zidan boshlab yangi stavka ishlaydi, o'tgan oylar "
                 "eski stavkada qoladi — to'langan oylik qayta "
                 "hisoblanmaydi."),
    }


@app.put("/api/career/grades/{key}")
def update_grade(
    key: str,
    payload: schemas.GradeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Daraja jadvalini tahrirlash. Hujjatning o'zida "talablar
    o'zgarib turishi mumkin" deb yozilgan — shuning uchun raqamlar
    kodda emas, shu yerda."""
    g = db.query(models.TeacherGrade).filter(
        models.TeacherGrade.key == key).first()
    if not g:
        raise HTTPException(404, "Daraja topilmadi")
    given = payload.model_dump(exclude_unset=True)
    rate_changed = ("rate_per_student" in given
                    and given["rate_per_student"] != g.rate_per_student)
    for k, v in given.items():
        setattr(g, k, v)
    db.commit()

    # Narx o'zgargan bo'lsa - shu darajadagi ustozlarning guruhlariga
    # ham qo'yiladi (qo'lda narx qo'yilganlaridan tashqari).
    touched = 0
    if rate_changed:
        for t in db.query(models.Teacher).filter(
                models.Teacher.grade == key).all():
            touched += _sync_group_rates(db, t, g.rate_per_student or 0)
        db.commit()
    return {"ok": True, "groups_updated": touched}


@app.get("/api/teachers/{teacher_id}/career")
def teacher_career(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Bitta ustozning karyera kartasi: hozirgi daraja, nima
    yetishmayapti, tarix va o'qish rejasi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    mine = _teacher_of_user(db, user)
    if user.role not in roles.CAREER_ACCESS and (
            not mine or mine.id != t.id):
        raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")

    st = _grade_state(db, t)
    history = (db.query(models.TeacherGradeEvent)
               .filter(models.TeacherGradeEvent.teacher_id == t.id)
               .order_by(models.TeacherGradeEvent.effective_from.desc(),
                         models.TeacherGradeEvent.id.desc()).all())

    stages = []
    for key, label, _b, _p in roles.STUDY_STAGES:
        items = _study_items(db, t, key)
        stages.append({
            "key": key, "label": label,
            "done": sum(1 for i in items if i.done),
            "total": len(items),
            "items": [{
                "id": i.id, "kind": i.kind, "title": i.title,
                "done": bool(i.done),
                "done_at": i.done_at.isoformat() if i.done_at else None,
                "note": i.note,
            } for i in sorted(items, key=lambda x: (x.kind != "book",
                                                    x.id))],
        })

    return {
        "state": st,
        "grades": [_grade_row_out(g) for g in _grade_rows(db)],
        "history": [{
            "id": e.id,
            "kind": e.kind,
            "kind_label": roles.GRADE_EVENT_LABELS.get(e.kind, e.kind),
            "tone": roles.GRADE_EVENT_TONE.get(e.kind, "slate"),
            "from_grade": e.from_grade,
            "from_label": roles.GRADE_LABELS.get(e.from_grade or ""),
            "to_grade": e.to_grade,
            "to_label": roles.GRADE_LABELS.get(e.to_grade or ""),
            "date": e.effective_from.isoformat() if e.effective_from else None,
            "reason": e.reason,
            "pass_rate": e.pass_rate,
            "test_avg": e.test_avg,
            "rate_before": e.rate_before,
            "rate_after": e.rate_after,
            "decided_by": e.decided_by,
        } for e in history],
        "study": stages,
        "entry": [{"key": k, "text": txt} for k, txt in roles.TEACHER_ENTRY],
        "can_edit": user.role in roles.GRADE_ADMIN,
        "is_me": bool(mine and mine.id == t.id),
    }


@app.post("/api/teachers/{teacher_id}/grade")
def set_teacher_grade(
    teacher_id: int,
    payload: schemas.GradeSet,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Darajani qo'lda qo'yish. Avtomat qaror noto'g'ri chiqqan bo'lsa
    shu yerdan qaytariladi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if payload.grade not in _grade_map(db):
        raise HTTPException(400, "Bunday daraja yo'q")
    if payload.grade == t.grade:
        return {"ok": True, "changed": False}
    _set_grade(db, t, payload.grade, kind="set",
               reason=payload.reason or "Qo'lda o'zgartirildi",
               by=user.full_name)
    db.commit()
    return {"ok": True, "changed": True,
            "grade": t.grade,
            "label": roles.GRADE_LABELS.get(t.grade, t.grade)}


@app.post("/api/teachers/{teacher_id}/remediation")
def clear_remediation(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Qayta test topshirildi — cheklovni olib tashlaymiz."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    t.remediation_until = None
    t.remediation_reason = None
    db.add(models.TeacherGradeEvent(
        teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
        kind="remediation_done", effective_from=date.today(),
        reason="Qayta test topshirildi", decided_by=user.full_name))
    db.commit()
    return {"ok": True}


@app.post("/api/teachers/{teacher_id}/study/{item_id}")
def mark_study(
    teacher_id: int,
    item_id: int,
    payload: schemas.StudyDone,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Kitob o'qildi / podkast ko'rildi. Ustoz o'zi belgilaydi."""
    item = db.query(models.TeacherStudyItem).get(item_id)
    if not item or item.teacher_id != teacher_id:
        raise HTTPException(404, "Topilmadi")
    mine = _teacher_of_user(db, user)
    if user.role not in roles.CAREER_ACCESS and (
            not mine or mine.id != teacher_id):
        raise HTTPException(403, "Faqat o'zingiznikini belgilay olasiz")
    item.done = 1 if payload.done else 0
    item.done_at = date.today() if payload.done else None
    if payload.note is not None:
        item.note = payload.note
    db.commit()
    return {"ok": True, "done": bool(item.done)}


@app.get("/api/me/career")
def my_career(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Ustozning O'Z karyera xaritasi: qaysi darajada, keyingisiga
    nima yetishmayapti, bir o'quvchidan qancha olyapti."""
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Sizning ustoz kartangiz topilmadi")
    return teacher_career(t.id, db=db, user=user)


@app.get("/api/teachers/scoreboard")
def teacher_scoreboard(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Ustozlar reytingi: dars sifati, retention, LTV va davomat.

    Ustozning o'ziga ochiq — hamkasblari orasidagi o'rnini ko'rsin.
    Lekin ularning MAOSHI bu yerda yo'q."""
    rows = _teacher_stats(db, months=months, branch_id=branch_id, user=user)
    me = None
    if user.role in (roles.TEACHER, roles.SUPPORT_TEACHER):
        t = _teacher_of_user(db, user)
        if t:
            me = next((r["teacher_id"] for r in rows
                       if r["teacher_id"] == t.id), None)

    def avg(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    return {
        "months": months,
        "rows": rows,
        "me": me,
        "count": len(rows),
        "dimensions": [{"key": k, "label": lbl, "weight": w}
                       for k, lbl, w in roles.TEACHER_SCORE_WEIGHTS],
        "averages": {
            "quality": avg("quality"),
            "retention": avg("retention"),
            "ltv": avg("ltv"),
            "attendance": avg("attendance"),
            "avg_months": avg("avg_months"),
            "score": avg("score"),
        },
    }


# =====================================================================
#  RUXSATLAR MATRITSASI
#
#  Ikki qavat: kod bilan keladigan standart (roles.DEFAULT_MATRIX) va
#  asoschi o'zgartirgan farq (RolePermission jadvali). Ikkinchisi
#  birinchisini bosadi.
#
#  Asoschining huquqini hech kim olib tashlay olmaydi - aks holda
#  tizimga kirish yo'li yopilib qolardi.
# =====================================================================
_PERM_CACHE: dict = {"data": None}


def _perm_overrides(db: Session) -> dict:
    """Bazadagi farqlar. Har o'zgarishda kesh tozalanadi."""
    if _PERM_CACHE["data"] is None:
        out: dict = {}
        try:
            for r in db.query(models.RolePermission).all():
                out.setdefault(r.role, {}).setdefault(r.resource, {})[r.action] = \
                    bool(r.allowed)
        except Exception:
            out = {}
        _PERM_CACHE["data"] = out
    return _PERM_CACHE["data"]


def perms_for(db: Session, role: str, resource: str) -> set:
    """Shu rol shu bo'limda nima qila oladi."""
    if role == roles.LOCKED_ROLE:
        return set(roles.PERM_ACTION_KEYS)
    allowed = roles.default_perms(role, resource)
    over = _perm_overrides(db).get(role, {}).get(resource, {})
    for action, ok in over.items():
        if ok:
            allowed.add(action)
        else:
            allowed.discard(action)
    return allowed


def has_perm(db: Session, user: models.User, resource: str,
             action: str = "view") -> bool:
    return action in perms_for(db, user.role, resource)


def require_perm(resource: str, action: str = "view"):
    """Endpoint himoyasi. Rol ro'yxatlari o'rniga ishlatiladi -
    shunda asoschi ruxsatni ekrandan o'zgartira oladi."""
    def dep(db: Session = Depends(get_db),
            user: models.User = Depends(get_current_user)):
        if not has_perm(db, user, resource, action):
            raise HTTPException(
                403,
                f"\"{roles.RESOURCE_LABELS.get(resource, resource)}\" bo'limida "
                f"\"{roles.PERM_ACTION_LABELS.get(action, action)}\" "
                f"ruxsatingiz yo'q")
        return user
    return dep


@app.get("/api/permissions")
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


@app.put("/api/permissions")
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


@app.post("/api/permissions/reset")
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


@app.get("/api/me/permissions")
def my_permissions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Foydalanuvchining o'z ruxsatlari. Frontend menyuni shunga
    qarab quradi — ko'rmaydigan bo'lim menyuda ham chiqmaydi."""
    return {
        "role": user.role,
        "role_label": roles.UZ_LABELS.get(user.role, user.role),
        "perms": {res: sorted(perms_for(db, user.role, res))
                  for res in roles.RESOURCE_KEYS},
    }


# =====================================================================
#  HAR BIR XODIMGA O'Z DASHBOARDI
#
#  Xodim kirganda BOSHQANING raqamini emas, O'ZINING ishini ko'radi.
#  Ustozga darslari va oyligi, administratorga qarzdorlari, HR'ga
#  nomzodlari. Umumiy raqamlar faqat rahbariyatda.
# =====================================================================
def _card(label: str, value, hint: str = None, tone: str = "plain",
          link: str = None) -> dict:
    return {"label": label, "value": value, "hint": hint,
            "tone": tone, "link": link}


def _my_teacher_cards(db: Session, user: models.User) -> list:
    t = _teacher_of_user(db, user)
    if not t:
        return []
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    earned = _teacher_earned(db, t.id, since=m_start)
    paid = _teacher_paid(db, t.id, since=m_start)
    balance = round(_teacher_earned(db, t.id)["amount"]
                    - _teacher_paid(db, t.id), 2)

    gids = [g.id for g in db.query(models.Group).filter(
        models.Group.teacher_id == t.id).all()]
    students = (db.query(models.Student).filter(
        models.Student.group_id.in_(gids or [-1]),
        models.Student.status == "active").count() if gids else 0)

    # Bugungi darslar
    todays = (db.query(models.Lesson).filter(
        models.Lesson.group_id.in_(gids or [-1]),
        models.Lesson.date == today).all() if gids else [])
    pending = [l for l in todays if not l.held]

    return [
        _card("Shu oy ishlab topgan", earned["amount"], 
              f"{earned['lessons']} dars · {earned['attendances']} yoqlama",
              "brand", "/teachers"),
        _card("Olgan puli", paid, "avans va oylik"),
        _card("Balans", balance,
              "sizga berilishi kerak" if balance > 0
              else "ortiqcha olingan" if balance < 0 else "hisob yopilgan",
              "good" if balance > 0 else "bad" if balance < 0 else "plain"),
        _card("Guruhlarim", len(gids), f"{students} ta o'quvchi", "plain",
              "/groups"),
        _card("Bugungi darslar", len(todays),
              f"{len(pending)} tasiga yo'qlama qo'yilmagan"
              if pending else "hammasi yopilgan",
              "bad" if pending else "good", "/timetable"),
        _grade_card(db, t),
    ]


def _grade_card(db: Session, t: models.Teacher) -> dict:
    """Ustoz o'z darajasini va keyingisiga qancha qolganini ko'radi."""
    try:
        st = _grade_state(db, t)
    except Exception:
        return _card("Darajam", "—", None, "plain", "/my-career")
    if st["in_remediation"]:
        hint = f"Qayta test: {st['remediation_until']}"
        tone = "bad"
    elif st["ready"] and st["next_label"]:
        hint = f"{st['next_label']} ga tayyorsiz"
        tone = "good"
    elif st["next_label"]:
        n = len(st["missing"])
        hint = (f"{st['next_label']} gacha {n} ta shart"
                if n else f"Keyingisi: {st['next_label']}")
        tone = "plain"
    else:
        hint = "Eng yuqori daraja"
        tone = "brand"
    return _card("Darajam", st["grade_label"], hint, tone, "/my-career")


def _my_sales_cards(db: Session, user: models.User) -> list:
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())

    mine = db.query(models.Lead).filter(
        models.Lead.created_at >= d0)
    if user.branch_id:
        mine = mine.filter(models.Lead.branch_id == user.branch_id)
    leads = mine.all()
    converted = [l for l in leads if l.stage == "converted"]

    # O'zi qabul qilgan pul
    pays = db.query(models.Payment).filter(
        models.Payment.kind == "payment",
        models.Payment.created_by == user.full_name,
        models.Payment.created_at >= d0).all()

    debt_q = scope_to_branch(db.query(models.Student), models.Student, user)
    debtors = [s for s in debt_q.filter(
        models.Student.status.in_(["active", "trial"])).all()
        if student_balance(db, s.id) < 0]

    return [
        _card("Shu oy lidlarim", len(leads),
              f"{len(converted)} tasi o'quvchi bo'ldi", "brand", "/leads"),
        _card("Konversiya",
              round(len(converted) / len(leads) * 100, 1) if leads else 0.0,
              "foizda"),
        _card("Men qabul qilgan pul", round(sum(p.amount for p in pays), 2),
              f"{len(pays)} ta to'lov", "good", "/finance"),
        _card("Qarzdorlarim", len(debtors),
              f"{round(sum(abs(student_balance(db, s.id)) for s in debtors)):,}"
              .replace(",", " ") + " so'm", "bad", "/finance"),
    ]


def _my_hr_cards(db: Session, user: models.User) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())

    cands = db.query(models.Candidate).filter(
        models.Candidate.created_at >= d0).all()
    hired = [c for c in cands if c.stage == "hired"]
    open_vac = db.query(models.Vacancy).filter(
        models.Vacancy.status == "open").count()
    staff = db.query(models.User).filter(models.User.is_active == 1).count()

    # Onboardingi tugamagan xodimlar
    unfinished = 0
    for u in db.query(models.User).filter(models.User.is_active == 1).all():
        rows = _onboarding_rows(db, u.id)
        if any(r["done"] for r in rows) and not all(r["done"] for r in rows):
            unfinished += 1

    # Yaqinlashayotgan tug'ilgan kun va yubileylar
    dates = _staff_dates(db, user, days=roles.STAFF_DATE_HORIZON)
    soon = [r for r in dates if r["soon"]]
    nearest = dates[0] if dates else None

    return [
        _card("Ochiq vakansiyalar", open_vac, None, "brand", "/hr"),
        _card("Shu oy nomzodlar", len(cands),
              f"{len(hired)} tasi ishga olindi", "plain", "/hr"),
        _card("Xodimlar", staff, None, "plain", "/users"),
        _card("Onboarding tugamagan", unfinished,
              "checklist yopilmagan", "bad" if unfinished else "good", "/users"),
        _card("Yaqin sanalar", len(soon),
              (f"{nearest['full_name']} — {nearest['kind_label'].lower()}, "
               + ("bugun" if nearest["today"]
                  else f"{nearest['days_left']} kundan keyin"))
              if nearest else "yaqin kunlarda yo'q",
              "amber" if soon else "plain", "/hr"),
    ]


def _my_academic_cards(db: Session, user: models.User) -> list:
    today = date.today()
    groups = scope_to_branch(db.query(models.Group), models.Group, user).all()
    rooms = {r.id: r for r in db.query(models.Room).all()}
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user).all()

    weak = 0
    for g in groups:
        n = sum(1 for s in students
                if s.group_id == g.id and s.status == "active")
        cap = _group_capacity(g, rooms)
        if cap and n / cap * 100 < 50:
            weak += 1

    risky = db.query(models.RiskFlag).filter(
        models.RiskFlag.active == 1).count()
    no_att = sum(1 for l in db.query(models.Lesson).filter(
        models.Lesson.date == today, models.Lesson.held == 0).all())

    return [
        _card("Guruhlar", len(groups), None, "brand", "/groups"),
        _card("Bugun yo'qlama qo'yilmagan", no_att,
              "ustozlarga eslatish kerak" if no_att else "hammasi yopilgan",
              "bad" if no_att else "good", "/timetable"),
        _card("Xavf ostidagi o'quvchilar", risky, None,
              "bad" if risky else "good", "/academic"),
        _card("Bo'sh qolayotgan guruhlar", weak, "50% dan kam to'lgan",
              "bad" if weak else "good", "/academic"),
    ]


def _my_exam_cards(db: Session, user: models.User) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    exams = db.query(models.Exam).filter(models.Exam.date >= m_start).all()
    draft = [e for e in exams if (e.status or "done") == "draft"]
    done = [e for e in exams if e.status == "done"]
    return [
        _card("Shu oy imtihonlar", len(exams), None, "brand", "/audit"),
        _card("Tasdiq kutayotgan", len(draft), None,
              "bad" if draft else "good", "/audit"),
        _card("O'tkazilgan", len(done), None, "good", "/audit"),
    ]


def _my_facility_cards(db: Session, user: models.User) -> list:
    assets = scope_to_branch(db.query(models.Asset), models.Asset, user).all()
    broken = [a for a in assets if a.condition in ("repair", "broken")]
    low = [c for c in scope_to_branch(
        db.query(models.Consumable), models.Consumable, user).all()
        if c.min_qty is not None and c.qty <= c.min_qty]
    reqs = db.query(models.PurchaseRequest).filter(
        models.PurchaseRequest.status == "open").count()
    return [
        _card("Aktivlar", len(assets), None, "brand", "/inventory"),
        _card("Ta'mir kerak", len(broken), None,
              "bad" if broken else "good", "/inventory"),
        _card("Kam qolgan mahsulot", len(low), None,
              "bad" if low else "good", "/inventory"),
        _card("Ochiq xarid so'rovi", reqs, None,
              "amber" if reqs else "good", "/inventory"),
    ]


def _my_marketing_cards(db: Session, user: models.User) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())
    leads = db.query(models.Lead).filter(models.Lead.created_at >= d0).all()
    conv = [l for l in leads if l.stage == "converted"]
    spend = sum(e.amount for e in db.query(models.Expense).filter(
        models.Expense.category == "ads",
        models.Expense.date >= m_start).all())
    return [
        _card("Shu oy lidlar", len(leads), None, "brand", "/marketing"),
        _card("O'quvchiga aylandi", len(conv), None, "good", "/marketing"),
        _card("Reklama xarajati", round(spend, 2), None, "plain", "/marketing"),
        _card("Bitta lid narxi",
              round(spend / len(leads)) if leads else 0,
              "CAC", "plain", "/analytics"),
    ]


def _my_finance_cards(db: Session, user: models.User) -> list:
    today = date.today()
    period = today.isoformat()[:7]
    m_start, m_end = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())
    d1 = datetime.combine(m_end, datetime.max.time())

    income = sum(p.amount for p, _s in (
        db.query(models.Payment, models.Student)
        .join(models.Student, models.Payment.student_id == models.Student.id)
        .filter(models.Payment.kind == "payment",
                models.Payment.created_at >= d0,
                models.Payment.created_at <= d1).all()))
    exp, _c = _expenses_total(db, user, m_start, m_end, None)
    payroll = _payroll_total(db, user, period, None)
    profit = income - exp - payroll

    pending = db.query(models.Discount).filter(
        models.Discount.status == "pending").count()

    return [
        _card("Shu oy tushum", round(income, 2), None, "brand", "/finance"),
        _card("Chiqim", round(exp + payroll, 2),
              f"shundan ish haqi {payroll:,.0f}".replace(",", " "),
              "plain", "/finance"),
        _card("Sof foyda", round(profit, 2),
              f"rentabellik {round(profit / income * 100, 1)}%" if income
              else None,
              "good" if profit > 0 else "bad", "/finance"),
        _card("Tasdiq kutayotgan chegirma", pending, None,
              "amber" if pending else "good", "/finance"),
    ]


# Rol -> qaysi kartalar
_MY_CARDS = {
    roles.TEACHER: _my_teacher_cards,
    roles.SUPPORT_TEACHER: _my_teacher_cards,
    roles.HEAD_SUPPORT: _my_academic_cards,
    roles.SALES_MANAGER: _my_sales_cards,
    roles.ADMINISTRATOR: _my_sales_cards,
    roles.SALES_HEAD: _my_sales_cards,
    roles.HR_MANAGER: _my_hr_cards,
    roles.ACADEMIC_HEAD: _my_academic_cards,
    roles.EXAMINER: _my_exam_cards,
    roles.HEAD_EXAMINER: _my_exam_cards,
    roles.FACILITY_MANAGER: _my_facility_cards,
    roles.SMM_MANAGER: _my_marketing_cards,
    roles.FINANCE_DIRECTOR: _my_finance_cards,
    roles.ACCOUNTANT: _my_finance_cards,
}


@app.get("/api/me/dashboard")
def my_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Xodimning O'Z dashboardi. Har bir rol o'ziga tegishli raqamni
    ko'radi — birovning ishi uni chalg'itmaydi."""
    # AVTOMAT: tug'ilgan kun va yubiley eslatmalari. HR hisobiga kirgan
    # zahoti vazifa paydo bo'ladi — hech kim tugma bosmaydi.
    if user.role in roles.STAFF_DATES_ACCESS:
        try:
            _ensure_staff_date_tasks(db, user)
        except Exception:
            db.rollback()

    builder = _MY_CARDS.get(user.role)
    cards = builder(db, user) if builder else []

    # Vazifalar — hammada bor
    my_tasks = (db.query(models.Task)
                .filter((models.Task.assignee_id == user.id)
                        | (models.Task.watcher_id == user.id))
                .all())
    open_tasks = [t for t in my_tasks if t.status not in roles.TASK_CLOSED]
    overdue = [t for t in open_tasks
               if t.deadline and t.deadline < date.today()]

    return {
        "role": user.role,
        "role_label": roles.UZ_LABELS.get(user.role, user.role),
        "full_name": user.full_name,
        "branch": user.branch.name if user.branch else None,
        "cards": cards,
        "tasks": {
            "open": len(open_tasks),
            "overdue": len(overdue),
            "rows": [_task_out(db, t) for t in sorted(
                open_tasks,
                key=lambda t: (t.deadline or date.max))[:5]],
        },
        # Umumiy raqamlarni faqat rahbariyat ko'radi
        "show_company": has_perm(db, user, "pnl", "view"),
        # Butun markaz bo'yicha kartalar (o'quvchilar soni, tushum,
        # qarzdorlar, xodimlar soni) — Examiner, HR va SMM'ga kerak
        # emas: ular faqat o'z ishini ko'radi.
        "show_general": user.role in tuple(roles.GENERAL_DASHBOARD),
    }


# =====================================================================
#  MENING PROFILIM
#  Har bir xodim o'z ish haqi holatini ko'radi: fiks, KPI, bonus.
# =====================================================================
@app.get("/api/me/profile")
def my_profile(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)
    period = today.isoformat()[:7]

    fix = user.fix_salary or 0.0
    parts = []
    total = fix
    if fix:
        parts.append({"key": "fix", "label": "Fiks oylik", "amount": fix,
                      "hint": "har oy o'zgarmas"})

    # --- Ustoz bo'lsa: yoqlamadan hisoblangan ish haqi ---
    t = _teacher_of_user(db, user)
    teacher_block = None
    if t:
        e = _teacher_earned(db, t.id, since=m_start, until=m_end)
        paid_m = _teacher_paid(db, t.id, since=m_start, until=m_end)
        balance = round(_teacher_earned(db, t.id)["amount"]
                        - _teacher_paid(db, t.id), 2)
        total += e["amount"]
        parts.append({
            "key": "lessons", "label": "Yo'qlamadan",
            "amount": e["amount"],
            "hint": f"{e['lessons']} dars · {e['attendances']} yo'qlama",
        })
        teacher_block = {
            "teacher_id": t.id,
            "earned_month": e["amount"],
            "paid_month": paid_m,
            "balance": balance,
            "by_group": e["by_group"],
        }

    # --- KPI va bonus ---
    kpi = None
    if user.role in (roles.SALES_MANAGER, roles.ADMINISTRATOR,
                     roles.SALES_HEAD):
        try:
            k = admin_kpi(year=today.year, month=today.month, db=db, user=user)
            row = next((r for r in k.rows if r.user_id == user.id), None)
            if row:
                kpi = {
                    "active_students": row.active_students,
                    "expected": row.expected,
                    "collected": row.collected,
                    "collection_percent": row.collection_percent,
                    "collection_bonus": row.collection_bonus,
                    "new_clients": row.new_clients,
                    "new_client_bonus": row.new_client_bonus,
                    "total": row.total,
                }
                bonus = (row.collection_bonus or 0) + (row.new_client_bonus or 0)
                if row.collection_bonus:
                    total += row.collection_bonus
                    parts.append({
                        "key": "collection",
                        "label": "To'lov yig'ish bonusi",
                        "amount": row.collection_bonus,
                        "hint": f"{row.collection_percent}% yig'ildi",
                    })
                if row.new_client_bonus:
                    total += row.new_client_bonus
                    parts.append({
                        "key": "new_clients",
                        "label": "Yangi mijoz bonusi",
                        "amount": row.new_client_bonus,
                        "hint": f"{row.new_clients} ta yangi o'quvchi",
                    })
        except Exception:
            kpi = None

    # --- Qo'lda berilgan bonuslar (xodim kartasidagi voqealar) ---
    manual = [e for e in db.query(models.StaffEvent).filter(
        models.StaffEvent.user_id == user.id,
        models.StaffEvent.kind == "bonus").all()
        if e.happened_on and m_start <= e.happened_on <= m_end]
    if manual:
        amt = sum(e.amount or 0 for e in manual)
        total += amt
        parts.append({"key": "bonus", "label": "Qo'shimcha bonus",
                      "amount": amt,
                      "hint": f"{len(manual)} ta"})

    # --- Jarimalar / ushlab qolishlar: kechikish va intizom ---
    late = [e for e in db.query(models.StaffEvent).filter(
        models.StaffEvent.user_id == user.id,
        models.StaffEvent.kind == "late").all()
        if e.happened_on and m_start <= e.happened_on <= m_end]

    onb = _onboarding_rows(db, user.id)
    onb_done = sum(1 for r in onb if r["done"])

    return {
        "id": user.id,
        "public_id": user.public_id,
        "full_name": user.full_name,
        "username": user.username,
        "role": user.role,
        "role_label": roles.UZ_LABELS.get(user.role, user.role),
        "position": user.position or roles.UZ_LABELS.get(user.role, user.role),
        "branch": user.branch.name if user.branch else None,
        "phone": user.phone,
        "photo": user.photo,
        "hired_date": (user.hired_date or
                       (user.created_at.date() if user.created_at else None)
                       ).isoformat() if (user.hired_date or user.created_at)
                      else None,
        "period": period,
        # Ish haqi holati
        "parts": parts,
        "total": round(total, 2),
        "fix_salary": fix,
        "teacher": teacher_block,
        "kpi": kpi,
        "late_count": len(late),
        "late_minutes": sum(e.minutes or 0 for e in late),
        "onboarding_done": onb_done,
        "onboarding_total": len(onb),
        "onboarding": onb,
    }


# =====================================================================
#  DARS JADVALI — XONA x VAQT TO'RI
#
#  Qatorlar - xonalar, ustunlar - 30 daqiqalik oraliqlar. Har bir
#  guruh o'z vaqtida to'g'ridan-to'g'ri turadi, shuning uchun bo'sh
#  xona va bo'sh soat bir qarashda ko'rinadi.
# =====================================================================
GRID_START_MIN = 6 * 60      # 06:00
GRID_END_MIN = 22 * 60       # 22:00
GRID_STEP = 30


def _grid_slots() -> list:
    out = []
    t = GRID_START_MIN
    while t < GRID_END_MIN:
        out.append(f"{t // 60:02d}:{t % 60:02d}")
        t += GRID_STEP
    return out


# Fan bo'yicha rang - jadvalda ko'z bilan ajratish uchun
SUBJECT_HUE = {
    "english": "teal",
    "russian": "violet",
    "korean": "emerald",
    "turkish": "amber",
    "german": "rose",
}

DAY_PRESETS = [
    ("odd", "Toq kunlar", ["mon", "wed", "fri"]),
    ("even", "Juft kunlar", ["tue", "thu", "sat"]),
]


@app.get("/api/timetable/grid")
def timetable_grid(
    day: str = "mon",
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_perm("timetable", "view")),
):
    """Xona x vaqt to'ri. day - hafta kuni yoki "odd"/"even"."""
    preset = next((p for p in DAY_PRESETS if p[0] == day), None)
    days = preset[2] if preset else [day]
    if not preset and day not in roles.WEEKDAY_KEYS:
        raise HTTPException(400, "Noto'g'ri kun")

    rooms = scope_to_branch(db.query(models.Room), models.Room,
                            user, branch_id).filter(
        models.Room.active == 1).order_by(models.Room.name).all()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    today = date.today()

    # Guruh bo'yicha: o'quvchilar, o'tilgan darslar, o'rtacha yosh
    held = {}
    for gid, cnt in (db.query(models.Lesson.group_id,
                              func.count(models.Lesson.id))
                     .filter(models.Lesson.held == 1)
                     .group_by(models.Lesson.group_id).all()):
        held[gid] = cnt

    # DIQQAT: Group.room - bu ESKI matnli ustun, bog'lanish emas.
    # Xona nomini har doim room_id orqali topamiz.
    room_by_id = {r.id: r for r in db.query(models.Room).all()}

    items, unplaced = [], []
    for g in groups:
        g_days = [d for d in (g.lesson_days or "").split(",") if d]
        start, end = _group_slot(g)
        mine = [s for s in students
                if s.group_id == g.id and s.status in ("active", "trial")]
        cap = _group_capacity(g, room_by_id)
        ages = [round((today - s.birth_date).days / 365.25, 1)
                for s in mine if s.birth_date]
        avg_age = round(sum(ages) / len(ages), 1) if ages else None

        row = {
            "group_id": g.id,
            "group": g.name,
            "subject": g.subject,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "", None),
            "level": g.level,
            "level_label": roles.LEVEL_LABELS.get(g.level or "", None),
            "teacher_id": g.teacher_id,
            "teacher": g.teacher.full_name if g.teacher else None,
            "room_id": g.room_id,
            "room": (room_by_id[g.room_id].name if g.room_id in room_by_id
                     else (g.room or None)),
            "days": g_days,
            "start": start,
            "end": end,
            "time_label": f"{start} - {end}" if start else None,
            "students": len(mine),
            "capacity": cap,
            "fill": round(len(mine) / cap * 100, 1) if cap else None,
            "lessons_held": held.get(g.id, 0),
            "avg_age": avg_age,
            "hue": SUBJECT_HUE.get(g.subject or "", "slate"),
            # To'la yoki juda bo'sh guruhni ko'z ilg'ashi kerak
            "warn": ("full" if cap and len(mine) >= cap
                     else "empty" if cap and len(mine) / cap < 0.5
                     else None),
        }
        if not g_days or not start:
            unplaced.append(row)
            continue
        if not any(d in days for d in g_days):
            continue
        items.append(row)

    slots = _grid_slots()

    def slot_index(t: str) -> int:
        m = roles.time_to_minutes(t)
        if m is None:
            return 0
        return max(0, (m - GRID_START_MIN) // GRID_STEP)

    # Xona bo'yicha joylashtiramiz
    by_room = {r.id: [] for r in rooms}
    no_room = []
    for it in items:
        it["col"] = slot_index(it["start"])
        e = roles.time_to_minutes(it["end"]) or 0
        s0 = roles.time_to_minutes(it["start"]) or 0
        it["span"] = max(1, (e - s0) // GRID_STEP)
        if it["room_id"] in by_room:
            by_room[it["room_id"]].append(it)
        else:
            no_room.append(it)

    # To'qnashuv: bir xonada vaqti kesishgan ikki guruh
    clashes = []
    for rid, rows in by_room.items():
        rows.sort(key=lambda x: x["col"])
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if roles.ranges_overlap(rows[i]["start"], rows[i]["end"],
                                        rows[j]["start"], rows[j]["end"]):
                    room = next((r for r in rooms if r.id == rid), None)
                    clashes.append({
                        "room": room.name if room else "—",
                        "time": rows[i]["time_label"],
                        "groups": [rows[i]["group"], rows[j]["group"]],
                    })

    # Xona samaradorligi: shu kunda necha soat band
    def busy_hours(rows):
        mins = 0
        for x in rows:
            a = roles.time_to_minutes(x["start"]) or 0
            b = roles.time_to_minutes(x["end"]) or 0
            mins += max(0, b - a)
        return round(mins / 60, 1)

    window = (GRID_END_MIN - GRID_START_MIN) / 60

    return {
        "day": day,
        "day_label": (preset[1] if preset
                      else roles.WEEKDAY_LABELS.get(day, day)),
        "days": days,
        "presets": [{"key": k, "label": lbl, "days": ds}
                    for k, lbl, ds in DAY_PRESETS],
        "weekdays": [{"key": k, "label": lbl, "short": sh}
                     for k, lbl, sh in roles.WEEKDAYS],
        "slots": slots,
        "start": slots[0],
        "step": GRID_STEP,
        "rooms": [{
            "id": r.id,
            "name": r.name,
            "capacity": r.capacity,
            "branch": r.branch.name if r.branch else None,
            "items": by_room.get(r.id, []),
            "busy_hours": busy_hours(by_room.get(r.id, [])),
            "usage": round(busy_hours(by_room.get(r.id, [])) / window * 100, 1),
        } for r in rooms],
        "no_room": no_room,
        "unplaced": unplaced,
        "clashes": clashes,
        "total_groups": len(items),
        "total_students": sum(i["students"] for i in items),
        "can_edit": has_perm(db, user, "timetable", "edit"),
        "can_export": has_perm(db, user, "timetable", "export"),
    }


# =====================================================================
#  LTV — MIJOZ QANCHA VAQT QOLADI VA QANCHA PUL KELTIRADI
#
#  Ikki xil LTV bor va ular chalkashmasligi kerak:
#    VAQT LTV - o'quvchi o'rtacha necha oy qoladi
#    PUL LTV  - shu vaqt ichida qancha to'laydi va qancha SOF FOYDA
#               qoldiradi
#
#  Sof foyda: to'lagan puli - ustoz haqi - unga to'g'ri keladigan
#  boshqa xarajat (ijara, kommunal, reklama o'quvchilar soniga bo'linadi).
# =====================================================================
def _student_payments(db: Session) -> dict:
    rows = (db.query(models.Payment.student_id,
                     func.sum(models.Payment.amount),
                     func.count(models.Payment.id))
            .filter(models.Payment.kind == "payment")
            .group_by(models.Payment.student_id).all())
    return {sid: {"total": amt or 0.0, "count": cnt or 0}
            for sid, amt, cnt in rows}


def _overhead_per_student_month(db: Session, user, branch_id=None) -> float:
    """Bitta o'quvchining bir oyiga to'g'ri keladigan umumiy xarajat
    (ustoz haqidan tashqari). Oxirgi 12 oyning o'rtachasi."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -11)
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)

    eq = db.query(models.Expense).filter(models.Expense.date >= start,
                                         models.Expense.date <= end)
    if branch_id:
        eq = eq.filter(models.Expense.branch_id == branch_id)
    elif user and user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        eq = eq.filter(models.Expense.branch_id == user.branch_id)
    total = sum(e.amount or 0 for e in eq.all())

    sq = scope_to_branch(db.query(models.Student), models.Student,
                         user, branch_id) if user else db.query(models.Student)
    active = sq.filter(models.Student.status == "active").count() or 1
    months = 12
    return round(total / months / active, 2)


def _teacher_cost_for_student(db: Session, s: models.Student,
                              groups: dict) -> float:
    """Shu o'quvchi uchun ustozga to'langan pul. Guruhning stavkasi
    va o'quvchi necha oy o'qiganidan chiqadi."""
    g = groups.get(s.group_id)
    if not g:
        return 0.0
    rate = g.teacher_rate_per_student or 0
    months = _months_between(s.enrolled_date or date.today(),
                             s.left_date or date.today())
    return round(rate * months, 2)


@app.get("/api/analytics/ltv")
def analytics_ltv(
    dimension: str = "overall",
    months: int = 24,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LTV_ACCESS)),
):
    """LTV to'liq tahlili.

    VAQT LTV: o'quvchi o'rtacha necha oy qoladi.
    PUL LTV:  o'rtacha qancha to'laydi va qancha sof foyda qoldiradi.

    Kesim: butun markaz / filial / ustoz / fan / guruh."""
    if dimension not in roles.LTV_DIMENSION_LABELS:
        raise HTTPException(400, "Noto'g'ri kesim")

    today = date.today()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    if not students:
        return {"dimension": dimension, "rows": [], "overall": None,
                "dimensions": [{"key": k, "label": l}
                               for k, l in roles.LTV_DIMENSIONS]}

    paid = _student_payments(db)
    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}
    overhead = _overhead_per_student_month(db, user, branch_id)

    def bucket_for(s):
        if dimension == "overall":
            return "all", "Butun o'quv markaz"
        if dimension == "branch":
            k = s.branch_id
            return str(k), (branches[k].name if k in branches
                            else "Filialsiz")
        if dimension == "group":
            k = s.group_id
            return str(k), (groups[k].name if k in groups else "Guruhsiz")
        if dimension == "subject":
            g = groups.get(s.group_id)
            k = g.subject if g else None
            return str(k), (roles.SUBJECT_LABELS.get(k or "", None)
                            or "Fan belgilanmagan")
        g = groups.get(s.group_id)
        k = g.teacher_id if g else None
        return str(k), (teachers[k].full_name if k in teachers
                        else "Ustoz biriktirilmagan")

    buckets: dict = {}
    for s in students:
        key, label = bucket_for(s)
        b = buckets.setdefault(key, {
            "key": key, "label": label,
            "students": 0, "active": 0, "left": 0,
            "months_sum": 0.0, "revenue": 0.0, "profit": 0.0,
            "payments": 0, "finished_months": [],
        })
        span = _months_between(s.enrolled_date or today,
                               s.left_date or today)
        rev = paid.get(s.id, {}).get("total", 0.0)
        t_cost = _teacher_cost_for_student(db, s, groups)
        profit = rev - t_cost - overhead * span

        b["students"] += 1
        b["months_sum"] += span
        b["revenue"] += rev
        b["profit"] += profit
        b["payments"] += paid.get(s.id, {}).get("count", 0)
        if s.left_date:
            b["left"] += 1
            b["finished_months"].append(span)
        elif s.status == "active":
            b["active"] += 1

    rows = []
    for b in buckets.values():
        n = b["students"] or 1
        fin = b["finished_months"]
        rows.append({
            "key": b["key"],
            "label": b["label"],
            "students": b["students"],
            "active": b["active"],
            "left": b["left"],
            # --- VAQT LTV ---
            "avg_months": round(b["months_sum"] / n, 1),
            # Faqat KETGANLAR bo'yicha - bu haqiqiy "umr", hali
            # o'qiyotganlar buni pasaytirmaydi
            "finished_avg_months": (round(sum(fin) / len(fin), 1)
                                    if fin else None),
            "longest_months": round(max(fin), 1) if fin else None,
            # --- PUL LTV ---
            "avg_revenue": round(b["revenue"] / n, 0),
            "avg_profit": round(b["profit"] / n, 0),
            "total_revenue": round(b["revenue"], 2),
            "total_profit": round(b["profit"], 2),
            "avg_payments": round(b["payments"] / n, 1),
            # Bir oyda o'rtacha qancha keltiradi
            "revenue_per_month": (round(b["revenue"] / b["months_sum"], 0)
                                  if b["months_sum"] else 0),
            "margin": (round(b["profit"] / b["revenue"] * 100, 1)
                       if b["revenue"] else 0.0),
            "churn": (round(b["left"] / n * 100, 1)),
        })
    rows.sort(key=lambda r: -r["avg_profit"])

    # Umumiy
    tot_students = sum(r["students"] for r in rows) or 1
    tot_months = sum(r["avg_months"] * r["students"] for r in rows)
    tot_rev = sum(r["total_revenue"] for r in rows)
    tot_profit = sum(r["total_profit"] for r in rows)
    overall = {
        "students": tot_students,
        "avg_months": round(tot_months / tot_students, 1),
        "avg_revenue": round(tot_rev / tot_students, 0),
        "avg_profit": round(tot_profit / tot_students, 0),
        "total_revenue": round(tot_rev, 2),
        "total_profit": round(tot_profit, 2),
        "margin": round(tot_profit / tot_rev * 100, 1) if tot_rev else 0.0,
        "overhead_per_month": overhead,
    }

    return {
        "dimension": dimension,
        "dimension_label": roles.LTV_DIMENSION_LABELS[dimension],
        "dimensions": [{"key": k, "label": l}
                       for k, l in roles.LTV_DIMENSIONS],
        "rows": rows,
        "overall": overall,
        "hint": ("Vaqt LTV — o'quvchi o'rtacha necha oy qoladi. "
                 "Pul LTV — shu vaqt ichida qancha to'laydi va "
                 "qancha sof foyda qoldiradi (ustoz haqi va "
                 "xarajat chiqarilgach)."),
    }


# =====================================================================
#  CHURN — kim, qayerdan va NEGA ketyapti
# =====================================================================
@app.post("/api/students/{student_id}/leave-reason")
def set_leave_reason(
    student_id: int,
    payload: schemas.LeaveReasonCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.reason not in roles.LEAVE_REASON_LABELS:
        raise HTTPException(400, "Noto'g'ri sabab")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    row = models.LeaveReason(
        student_id=s.id, reason=payload.reason, note=payload.note,
        group_id=s.group_id, teacher_id=g.teacher_id if g else None,
        left_date=s.left_date or date.today(),
        created_by=user.full_name)
    db.add(row); db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Ketish sababi",
              new_value=roles.LEAVE_REASON_LABELS[payload.reason],
              commit=True)
    return {"ok": True}


@app.get("/api/analytics/churn")
def analytics_churn(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LTV_ACCESS)),
):
    """Qaysi guruhdan va qaysi ustozdan ko'p ketyapti — va NEGA."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}

    reasons = {}
    for r in db.query(models.LeaveReason).all():
        reasons[r.student_id] = r

    left = [s for s in students if s.left_date and s.left_date >= start]
    active = [s for s in students if s.status == "active"]

    # --- Sabablar ---
    by_reason = {}
    for s in left:
        r = reasons.get(s.id)
        key = r.reason if r else "unknown"
        row = by_reason.setdefault(key, {
            "key": key,
            "label": roles.LEAVE_REASON_LABELS.get(key, key),
            "group": roles.LEAVE_REASON_GROUP.get(key, "unknown"),
            "controllable": key in roles.CONTROLLABLE_REASONS,
            "count": 0, "students": [],
        })
        row["count"] += 1
        if len(row["students"]) < 10:
            row["students"].append(s.full_name)
    reason_rows = sorted(by_reason.values(), key=lambda r: -r["count"])

    # --- Ustoz kesimi ---
    def bucket(items, key_fn, label_fn):
        out = {}
        for s in items:
            k = key_fn(s)
            row = out.setdefault(str(k), {
                "key": k, "label": label_fn(k),
                "left": 0, "active": 0, "reasons": {},
            })
            if s.left_date and s.left_date >= start:
                row["left"] += 1
                r = reasons.get(s.id)
                rk = r.reason if r else "unknown"
                row["reasons"][rk] = row["reasons"].get(rk, 0) + 1
            elif s.status == "active":
                row["active"] += 1
        rows = []
        for r in out.values():
            base = r["left"] + r["active"]
            top = max(r["reasons"].items(), key=lambda x: x[1])[0] \
                if r["reasons"] else None
            rows.append({
                **r,
                "total": base,
                "churn": round(r["left"] / base * 100, 1) if base else 0.0,
                "top_reason": top,
                "top_reason_label": (roles.LEAVE_REASON_LABELS.get(top, None)
                                     if top else None),
                "reasons": [{"key": k, "label": roles.LEAVE_REASON_LABELS.get(k, k),
                             "count": v}
                            for k, v in sorted(r["reasons"].items(),
                                               key=lambda x: -x[1])],
            })
        rows.sort(key=lambda r: (-r["churn"], -r["left"]))
        return [r for r in rows if r["total"] > 0]

    by_teacher = bucket(
        students,
        lambda s: (groups[s.group_id].teacher_id
                   if s.group_id in groups else None),
        lambda k: teachers[k].full_name if k in teachers else "Biriktirilmagan")
    by_group = bucket(
        students,
        lambda s: s.group_id,
        lambda k: groups[k].name if k in groups else "Guruhsiz")

    total_base = len(left) + len(active)
    controllable = sum(r["count"] for r in reason_rows if r["controllable"])
    unknown = sum(r["count"] for r in reason_rows if r["key"] == "unknown")

    return {
        "months": months,
        "period": f"{start.isoformat()} — {today.isoformat()}",
        "left": len(left),
        "active": len(active),
        "churn": round(len(left) / total_base * 100, 1) if total_base else 0.0,
        "reasons": reason_rows,
        "by_teacher": by_teacher,
        "by_group": by_group,
        "controllable": controllable,
        "controllable_percent": (round(controllable / len(left) * 100, 1)
                                 if left else 0.0),
        "unknown": unknown,
        "reason_options": [{"key": k, "label": lbl}
                           for k, lbl, _ in roles.LEAVE_REASONS],
        "hint": ("Bizga bog'liq sabablar — ustoz, natija, raqobatchi, "
                 "jadval. Shularni kamaytirish mumkin."),
    }


# =====================================================================
#  XODIMLAR DAVOMATI
#  Kechikish daqiqasi AVTOMAT hisoblanadi — qo'lda yozilmaydi, aks
#  holda hech kim o'zini kechikkan deb yozmaydi.
# =====================================================================
def _minutes(t: str) -> int | None:
    return roles.time_to_minutes(t)


@app.post("/api/hr/attendance")
def mark_staff_attendance(
    payload: schemas.StaffAttendanceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_ACCESS)),
):
    emp = db.query(models.User).get(payload.user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    on = payload.date or date.today()

    row = (db.query(models.StaffAttendance)
           .filter(models.StaffAttendance.user_id == emp.id,
                   models.StaffAttendance.work_date == on).first())
    if not row:
        row = models.StaffAttendance(user_id=emp.id, work_date=on,
                                     created_by=user.full_name)
        db.add(row)

    if payload.check_in is not None:
        row.check_in = payload.check_in
    if payload.check_out is not None:
        row.check_out = payload.check_out
    if payload.note is not None:
        row.note = payload.note

    # Kechikish va erta ketish — avtomat
    start = _minutes(roles.WORK_START) or 0
    end = _minutes(roles.WORK_END) or 0
    ci = _minutes(row.check_in or "")
    co = _minutes(row.check_out or "")

    row.late_minutes = (max(0, ci - start - roles.LATE_TOLERANCE_MIN)
                        if ci is not None else 0)
    row.early_minutes = (max(0, end - co) if co is not None else 0)
    row.worked_minutes = (max(0, co - ci) if ci is not None and co is not None
                          else 0)
    db.commit(); db.refresh(row)
    return _attendance_out(row, emp)


def _attendance_out(r: models.StaffAttendance, emp=None) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "full_name": emp.full_name if emp else None,
        "date": r.work_date.isoformat() if r.work_date else None,
        "check_in": r.check_in,
        "check_out": r.check_out,
        "late_minutes": r.late_minutes or 0,
        "early_minutes": r.early_minutes or 0,
        "worked_minutes": r.worked_minutes or 0,
        "worked_hours": round((r.worked_minutes or 0) / 60, 1),
        "note": r.note,
    }


@app.get("/api/hr/attendance")
def staff_attendance(
    year: int | None = None,
    month: int | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_ACCESS)),
):
    today = date.today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)

    staff = db.query(models.User).filter(
        models.User.is_active == 1,
        ~models.User.role.in_(roles.EXTERNAL_ROLES)).all()
    if user_id:
        staff = [u for u in staff if u.id == user_id]
    ids = [u.id for u in staff]

    rows = (db.query(models.StaffAttendance)
            .filter(models.StaffAttendance.user_id.in_(ids or [-1]),
                    models.StaffAttendance.work_date >= start,
                    models.StaffAttendance.work_date <= end).all())

    by_user = {}
    for r in rows:
        by_user.setdefault(r.user_id, []).append(r)

    summary = []
    for u in staff:
        mine = by_user.get(u.id, [])
        late = [r for r in mine if (r.late_minutes or 0) > 0]
        summary.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "role_label": roles.UZ_LABELS.get(u.role, u.role),
            "branch": u.branch.name if u.branch else None,
            "days": len(mine),
            "late_days": len(late),
            "late_minutes": sum(r.late_minutes or 0 for r in mine),
            "early_minutes": sum(r.early_minutes or 0 for r in mine),
            "worked_hours": round(
                sum(r.worked_minutes or 0 for r in mine) / 60, 1),
            "rows": [_attendance_out(r) for r in
                     sorted(mine, key=lambda x: x.work_date or date.min,
                            reverse=True)],
        })
    summary.sort(key=lambda r: -r["late_minutes"])

    return {
        "period": f"{y:04d}-{m:02d}",
        "work_start": roles.WORK_START,
        "work_end": roles.WORK_END,
        "tolerance": roles.LATE_TOLERANCE_MIN,
        "rows": summary,
        "total_late_minutes": sum(r["late_minutes"] for r in summary),
        "staff_with_late": sum(1 for r in summary if r["late_days"] > 0),
    }


# =====================================================================
#  USTOZLAR NPS
#  O'quvchi va ota-ona ustozga 0-10 baho beradi.
#  NPS = tarafdorlar% - tanqidchilar%
# =====================================================================
@app.post("/api/nps")
def add_rating(
    payload: schemas.RatingCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    t = db.query(models.Teacher).get(payload.teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if not (0 <= payload.score <= 10):
        raise HTTPException(400, "Baho 0 dan 10 gacha bo'lishi kerak")
    if payload.source not in roles.NPS_SOURCE_LABELS:
        raise HTTPException(400, "Noto'g'ri manba")

    s = (db.query(models.Student).get(payload.student_id)
         if payload.student_id else None)
    r = models.TeacherRating(
        teacher_id=t.id, student_id=payload.student_id,
        group_id=s.group_id if s else None,
        source=payload.source, score=payload.score,
        comment=payload.comment,
        period=date.today().isoformat()[:7],
        created_by=user.full_name)
    db.add(r); db.commit()
    return {"id": r.id, "band": roles.nps_band(payload.score)[1]}


@app.get("/api/nps")
def nps_report(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NPS_ACCESS)),
):
    """Ustozlar NPS'i. Ustozning o'ziga ham ochiq — lekin o'zining
    bahosi, hamkasbining emas."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    d0 = datetime.combine(start, datetime.min.time())

    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher,
                               user, branch_id).all()
    ids = [t.id for t in teachers]
    rows = (db.query(models.TeacherRating)
            .filter(models.TeacherRating.teacher_id.in_(ids or [-1]),
                    models.TeacherRating.created_at >= d0).all())

    by_t = {}
    for r in rows:
        by_t.setdefault(r.teacher_id, []).append(r)

    out = []
    for t in teachers:
        mine = by_t.get(t.id, [])
        if not mine:
            continue
        scores = [r.score for r in mine]
        pro = sum(1 for s in scores if s >= 9)
        pas = sum(1 for s in scores if 7 <= s <= 8)
        det = sum(1 for s in scores if s <= 6)
        out.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "answers": len(scores),
            "avg": round(sum(scores) / len(scores), 1),
            "nps": roles.nps_value(scores),
            "promoters": pro,
            "passives": pas,
            "detractors": det,
            "by_student": roles.nps_value(
                [r.score for r in mine if r.source == "student"]),
            "by_parent": roles.nps_value(
                [r.score for r in mine if r.source == "parent"]),
            "comments": [{
                "score": r.score,
                "band": roles.nps_band(r.score)[0],
                "source": roles.NPS_SOURCE_LABELS.get(r.source, r.source),
                "comment": r.comment,
                "date": r.created_at.date().isoformat() if r.created_at else None,
            } for r in sorted(mine, key=lambda x: x.created_at or datetime.min,
                              reverse=True)[:10] if r.comment],
        })
    out.sort(key=lambda r: -r["nps"])

    all_scores = [r.score for r in rows]
    return {
        "months": months,
        "rows": out,
        "overall_nps": roles.nps_value(all_scores),
        "answers": len(all_scores),
        "avg": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "sources": [{"key": k, "label": lbl} for k, lbl in roles.NPS_SOURCES],
        "bands": [{"key": k, "label": lbl, "tone": t, "min": mn}
                  for mn, k, lbl, t in roles.NPS_BANDS],
        "hint": ("NPS = tarafdorlar foizi − tanqidchilar foizi. "
                 "0 dan yuqori — yaxshi, 50 dan yuqori — a'lo."),
    }


# =====================================================================
#  ROMI — REKLAMA SAMARADORLIGI
#  ROMI = (kanal keltirgan foyda − kanal xarajati) / kanal xarajati × 100
#  100% dan yuqori — pul ishlayapti. 0 dan past — zarar.
# =====================================================================
@app.get("/api/analytics/romi")
def analytics_romi(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(start, datetime.min.time())

    leads = db.query(models.Lead).filter(models.Lead.created_at >= d0)
    if branch_id:
        leads = leads.filter(models.Lead.branch_id == branch_id)
    elif user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        leads = leads.filter(models.Lead.branch_id == user.branch_id)
    leads = leads.all()

    # Kanal xarajati: reklama xarajatlari channel bo'yicha
    spend = {}
    eq = db.query(models.Expense).filter(
        models.Expense.date >= start, models.Expense.date <= end,
        models.Expense.category == "ads")
    if branch_id:
        eq = eq.filter(models.Expense.branch_id == branch_id)
    for e in eq.all():
        ch = e.channel or "other"
        spend[ch] = spend.get(ch, 0.0) + (e.amount or 0)

    paid = _student_payments(db)
    students = {s.id: s for s in db.query(models.Student).all()}
    groups = {g.id: g for g in db.query(models.Group).all()}
    overhead = _overhead_per_student_month(db, user, branch_id)

    # Lidni o'quvchiga bog'lash - ism bo'yicha (converted lidlar)
    by_name = {}
    for s in students.values():
        by_name.setdefault(s.full_name.strip().lower(), s)

    by_channel = {}
    for l in leads:
        ch = l.source or "other"
        row = by_channel.setdefault(ch, {
            "key": ch,
            "label": roles.LEAD_SOURCE_LABELS.get(ch, ch)
                     if hasattr(roles, "LEAD_SOURCE_LABELS") else ch,
            "leads": 0, "converted": 0, "revenue": 0.0, "profit": 0.0,
        })
        row["leads"] += 1
        if l.stage == "converted":
            row["converted"] += 1
            s = by_name.get((l.full_name or "").strip().lower())
            if s:
                rev = paid.get(s.id, {}).get("total", 0.0)
                span = _months_between(s.enrolled_date or today,
                                       s.left_date or today)
                cost = _teacher_cost_for_student(db, s, groups) + overhead * span
                row["revenue"] += rev
                row["profit"] += rev - cost

    rows = []
    for r in by_channel.values():
        cost = spend.get(r["key"], 0.0)
        romi = (round((r["profit"] - cost) / cost * 100, 1)
                if cost else (None if r["profit"] == 0 else 9999.0))
        band, band_label, tone = roles.romi_band(romi if romi is not None else 0)
        rows.append({
            **r,
            "spend": round(cost, 2),
            "cac": round(cost / r["converted"], 0) if r["converted"] else None,
            "cpl": round(cost / r["leads"], 0) if r["leads"] else None,
            "conversion": (round(r["converted"] / r["leads"] * 100, 1)
                           if r["leads"] else 0.0),
            "revenue": round(r["revenue"], 2),
            "profit": round(r["profit"], 2),
            "romi": romi,
            "band": band if cost else "unknown",
            "band_label": band_label if cost else "Xarajat kiritilmagan",
            "tone": tone if cost else "slate",
        })
    rows.sort(key=lambda r: -(r["romi"] if r["romi"] is not None else -99999))

    total_spend = sum(r["spend"] for r in rows)
    total_profit = sum(r["profit"] for r in rows)
    return {
        "months": months,
        "period": f"{start.isoformat()} — {end.isoformat()}",
        "rows": rows,
        "total_spend": round(total_spend, 2),
        "total_revenue": round(sum(r["revenue"] for r in rows), 2),
        "total_profit": round(total_profit, 2),
        "romi": (round((total_profit - total_spend) / total_spend * 100, 1)
                 if total_spend else None),
        "no_spend": [r["label"] for r in rows if not r["spend"]],
        "hint": ("ROMI 100% dan yuqori bo'lsa — kanal o'z pulini "
                 "qaytarib, ustiga foyda keltiryapti. Xarajat "
                 "kiritilmagan kanallarda ROMI hisoblanmaydi."),
    }


# =====================================================================
#  XONALAR BANDLIGI — SIG'IMDAN NECHA FOIZ FOYDALANILYAPTI
#  Ikki xil bandlik bor:
#    O'RIN bandligi - xonadagi joylarning nechtasi to'lgan
#    VAQT bandligi  - xona haftada necha soat ishlatilyapti
# =====================================================================
@app.get("/api/analytics/capacity")
def analytics_capacity(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    rooms = scope_to_branch(db.query(models.Room), models.Room,
                            user, branch_id).filter(
        models.Room.active == 1).all()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    room_by_id = {r.id: r for r in rooms}

    # Haftada nechа soat ochiq: 6 kun x (22:00 - 06:00)
    open_hours_week = 6 * (GRID_END_MIN - GRID_START_MIN) / 60

    rows = []
    for r in rooms:
        mine = [g for g in groups if g.room_id == r.id]
        hours = 0.0
        seats_used = 0
        slots = 0
        for g in mine:
            days = len([d for d in (g.lesson_days or "").split(",") if d])
            a, b = _group_slot(g)
            if a and b:
                dur = ((roles.time_to_minutes(b) or 0)
                       - (roles.time_to_minutes(a) or 0)) / 60
                hours += dur * days
            n = sum(1 for s in students
                    if s.group_id == g.id and s.status in ("active", "trial"))
            seats_used += n
            slots += (r.capacity or 0)
        rows.append({
            "room_id": r.id,
            "name": r.name,
            "branch": r.branch.name if r.branch else None,
            "capacity": r.capacity,
            "groups": len(mine),
            "students": seats_used,
            # O'rin bandligi: guruhlar bo'yicha o'rtacha to'lish
            "seat_usage": round(seats_used / slots * 100, 1) if slots else 0.0,
            # Vaqt bandligi: haftada necha soat band
            "hours_week": round(hours, 1),
            "time_usage": round(hours / open_hours_week * 100, 1),
            "free_seats": max(0, slots - seats_used),
        })
    rows.sort(key=lambda r: r["time_usage"])

    total_cap = sum(r.capacity or 0 for r in rooms)
    total_students = sum(1 for s in students if s.status == "active")
    total_hours = sum(r["hours_week"] for r in rows)
    open_total = open_hours_week * len(rooms) if rooms else 1

    # Bo'sh joyning pul qiymati
    avg_fee = 0.0
    fees = [g.monthly_fee or 0 for g in groups if g.monthly_fee]
    if fees:
        avg_fee = sum(fees) / len(fees)
    lost = sum(r["free_seats"] for r in rows) * avg_fee

    return {
        "rooms": rows,
        "room_count": len(rooms),
        "total_capacity": total_cap,
        "active_students": total_students,
        # Umumiy sig'imdan necha foiz ishlatilyapti
        "seat_usage": (round(total_students / total_cap * 100, 1)
                       if total_cap else 0.0),
        "time_usage": round(total_hours / open_total * 100, 1) if rooms else 0.0,
        "open_hours_week": open_hours_week,
        "free_seats": sum(r["free_seats"] for r in rows),
        "lost_income": round(lost, 2),
        "worst": rows[0]["name"] if rows else None,
        "hint": ("Bo'sh turgan xona — bu ijara puli. Vaqt bandligi "
                 "past xonalarga yangi guruh qo'yish mumkin."),
    }


# =====================================================================
#  RFM SEGMENTATSIYA
#  R - oxirgi to'lovdan beri qancha vaqt o'tdi
#  F - nechta to'lov qilgan
#  M - jami qancha to'lagan
#  Har bir segment uchun ANIQ harakat taklif qilinadi — segment
#  o'zi hech narsani o'zgartirmaydi, harakat o'zgartiradi.
# =====================================================================
@app.get("/api/marketing/rfm")
def marketing_rfm(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    today = date.today()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).filter(
        models.Student.status != "archived").all()
    if not students:
        return {"rows": [], "segments": [], "total": 0}

    ids = [s.id for s in students]
    last = {}
    agg = {}
    for sid, mx, cnt, total in (
            db.query(models.Payment.student_id,
                     func.max(models.Payment.created_at),
                     func.count(models.Payment.id),
                     func.sum(models.Payment.amount))
            .filter(models.Payment.student_id.in_(ids),
                    models.Payment.kind == "payment")
            .group_by(models.Payment.student_id).all()):
        last[sid] = mx
        agg[sid] = (cnt or 0, total or 0.0)

    rows = []
    for s in students:
        cnt, total = agg.get(s.id, (0, 0.0))
        lastp = last.get(s.id)
        days = ((today - lastp.date()).days if lastp
                else (today - (s.enrolled_date or today)).days)
        r, f, m, seg = roles.rfm_score(days, cnt, total)
        info = roles.RFM_SEGMENT_INFO[seg]
        rows.append({
            "student_id": s.id,
            "full_name": s.full_name,
            "phone": s.phone or s.parent_phone,
            "group": s.group.name if s.group else None,
            "status": s.status,
            "r": r, "f": f, "m": m,
            "days_since_payment": days,
            "payments": cnt,
            "total_paid": round(total, 2),
            "balance": round(student_balance(db, s.id), 2),
            "segment": seg,
            "segment_label": info["label"],
            "tone": info["tone"],
            "action": info["action"],
        })

    by_seg = {}
    for r in rows:
        b = by_seg.setdefault(r["segment"], {"count": 0, "revenue": 0.0})
        b["count"] += 1
        b["revenue"] += r["total_paid"]

    segments = []
    for key, label, hint, tone, action in roles.RFM_SEGMENTS:
        b = by_seg.get(key, {"count": 0, "revenue": 0.0})
        segments.append({
            "key": key, "label": label, "hint": hint, "tone": tone,
            "action": action,
            "count": b["count"],
            "revenue": round(b["revenue"], 2),
            "percent": round(b["count"] / len(rows) * 100, 1) if rows else 0.0,
        })

    rows.sort(key=lambda r: (-r["m"], -r["f"], -r["r"]))
    return {
        "rows": rows,
        "segments": segments,
        "total": len(rows),
        "hint": ("R — oxirgi to'lovdan beri o'tgan vaqt, "
                 "F — to'lovlar soni, M — jami summa. "
                 "Har bir segment uchun aniq harakat taklif qilingan."),
    }


# =====================================================================
#  AVTOMATIK XABARNOMALAR
#  Tizim xabarni O'ZI yaratadi va navbatga qo'yadi: tug'ilgan kun,
#  to'lov eslatmasi, qarzdorlik, darsga kelmagan.
#
#  Yuborish uchun Telegram bot tokeni (TELEGRAM_BOT_TOKEN) yoki SMS
#  xizmati kerak. U bo'lmasa xabarlar navbatda turadi va qo'lda
#  ko'chirib yuborish mumkin.
# =====================================================================
def _ensure_templates(db: Session) -> None:
    have = {t.kind for t in db.query(models.NotifyTemplate).all()}
    for kind, (title, body) in roles.DEFAULT_TEMPLATES.items():
        if kind in have:
            continue
        db.add(models.NotifyTemplate(
            kind=kind, title=title, body=body,
            days_before=roles.NOTIFY_DEFAULT_DAYS.get(kind, 0)))
    db.commit()


def _fill(body: str, **kw) -> str:
    out = body
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v if v is not None else ""))
    return out


def _money(v) -> str:
    return f"{round(v or 0):,}".replace(",", " ")


@app.get("/api/notifications/templates")
def notify_templates(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    _ensure_templates(db)
    rows = db.query(models.NotifyTemplate).all()
    order = [k for k, _, _ in roles.NOTIFY_KINDS]
    rows.sort(key=lambda t: order.index(t.kind) if t.kind in order else 99)
    return {
        "rows": [{
            "id": t.id, "kind": t.kind,
            "kind_label": roles.NOTIFY_KIND_LABELS.get(t.kind, t.kind),
            "title": t.title, "body": t.body,
            "channel": t.channel, "active": bool(t.active),
            "days_before": t.days_before or 0,
        } for t in rows],
        "channels": [{"key": k, "label": lbl}
                     for k, lbl in roles.NOTIFY_CHANNELS],
        "placeholders": ["{ism}", "{summa}", "{sana}", "{guruh}", "{kurs}"],
        "telegram_ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
    }


@app.put("/api/notifications/templates/{tid}")
def update_template(
    tid: int,
    payload: schemas.TemplateUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    t = db.query(models.NotifyTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Shablon topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, 1 if k == "active" and v else (0 if k == "active" else v))
    db.commit()
    return {"ok": True}


@app.post("/api/notifications/generate")
def generate_notifications(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    """AVTOMAT: bugungi tug'ilgan kunlar, to'lov eslatmalari va
    qarzdorlik xabarlarini navbatga qo'yadi. Takror yaratilmaydi."""
    _ensure_templates(db)
    today = date.today()
    tpl = {t.kind: t for t in db.query(models.NotifyTemplate).all()
           if t.active}

    students = scope_to_branch(db.query(models.Student), models.Student,
                               user).filter(
        models.Student.status.in_(["active", "trial"])).all()

    made = {k: 0 for k in roles.NOTIFY_KIND_LABELS}

    def already(kind, sid, on):
        return (db.query(models.Notification)
                .filter(models.Notification.kind == kind,
                        models.Notification.student_id == sid,
                        models.Notification.scheduled_for == on).first())

    for s in students:
        phone = s.phone or s.parent_phone

        # --- Tug'ilgan kun ---
        t = tpl.get("birthday")
        if t and s.birth_date and (s.birth_date.month, s.birth_date.day) == \
                (today.month, today.day) and not already("birthday", s.id, today):
            db.add(models.Notification(
                kind="birthday", channel=t.channel, student_id=s.id,
                phone=phone, title=t.title,
                body=_fill(t.body, ism=s.full_name),
                scheduled_for=today, created_by="Tizim"))
            made["birthday"] += 1

        bal = student_balance(db, s.id)

        # --- Qarzdorlik ---
        t = tpl.get("debt")
        if t and bal < 0 and not already("debt", s.id, today):
            db.add(models.Notification(
                kind="debt", channel=t.channel, student_id=s.id,
                phone=phone, title=t.title,
                body=_fill(t.body, ism=s.full_name, summa=_money(abs(bal))),
                scheduled_for=today, created_by="Tizim"))
            made["debt"] += 1

        # --- To'lov eslatmasi: oy oxiriga N kun qolganda ---
        t = tpl.get("payment_due")
        if t and bal >= 0:
            _s0, m_end = billing.month_bounds(today.year, today.month)
            days_left = (m_end - today).days
            if days_left == (t.days_before or 3) and s.group:
                if not already("payment_due", s.id, today):
                    db.add(models.Notification(
                        kind="payment_due", channel=t.channel,
                        student_id=s.id, phone=phone, title=t.title,
                        body=_fill(t.body, ism=s.full_name,
                                   sana=m_end.isoformat(),
                                   summa=_money(s.group.monthly_fee)),
                        scheduled_for=today, created_by="Tizim"))
                    made["payment_due"] += 1

    db.commit()
    total = sum(made.values())
    return {
        "created": total,
        "by_kind": [{"key": k, "label": roles.NOTIFY_KIND_LABELS[k],
                     "count": v} for k, v in made.items() if v],
        "date": today.isoformat(),
    }


@app.get("/api/notifications")
def list_notifications(
    status_filter: str | None = None,
    kind: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    q = db.query(models.Notification)
    if status_filter:
        q = q.filter(models.Notification.status == status_filter)
    if kind:
        q = q.filter(models.Notification.kind == kind)
    rows = q.order_by(models.Notification.created_at.desc()).limit(300).all()

    counts = {}
    for n in db.query(models.Notification).all():
        counts[n.status] = counts.get(n.status, 0) + 1

    return {
        "rows": [{
            "id": n.id,
            "kind": n.kind,
            "kind_label": roles.NOTIFY_KIND_LABELS.get(n.kind, n.kind),
            "channel": n.channel,
            "channel_label": roles.NOTIFY_CHANNEL_LABELS.get(n.channel, n.channel),
            "student_id": n.student_id,
            "student": n.student.full_name if n.student else None,
            "phone": n.phone,
            "title": n.title,
            "body": n.body,
            "status": n.status,
            "status_label": roles.NOTIFY_STATUS_LABELS.get(n.status, n.status),
            "tone": roles.NOTIFY_STATUS_TONE.get(n.status, "slate"),
            "scheduled_for": (n.scheduled_for.isoformat()
                              if n.scheduled_for else None),
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "error": n.error,
        } for n in rows],
        "counts": counts,
        "statuses": [{"key": k, "label": lbl, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, lbl, t in roles.NOTIFY_STATUSES],
        "kinds": [{"key": k, "label": lbl}
                  for k, lbl, _ in roles.NOTIFY_KINDS],
        "telegram_ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
    }


@app.post("/api/notifications/{nid}/status")
def set_notification_status(
    nid: int,
    payload: schemas.NotifyStatus,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    n = db.query(models.Notification).get(nid)
    if not n:
        raise HTTPException(404, "Topilmadi")
    if payload.status not in roles.NOTIFY_STATUS_LABELS:
        raise HTTPException(400, "Noto'g'ri holat")
    n.status = payload.status
    if payload.status == "sent":
        n.sent_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.post("/api/notifications/custom")
def custom_notification(
    payload: schemas.NotifyCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.NOTIFY_ACCESS)),
):
    """Qo'lda xabar: yangi kurs, taklif va h.k. Segment bo'yicha
    bir vaqtda yuborish mumkin."""
    if not payload.body.strip():
        raise HTTPException(400, "Xabar matnini yozing")

    targets = []
    if payload.student_ids:
        targets = (db.query(models.Student)
                   .filter(models.Student.id.in_(payload.student_ids)).all())
    elif payload.segment:
        rfm = marketing_rfm(branch_id=None, db=db, user=user)
        ids = [r["student_id"] for r in rfm["rows"]
               if r["segment"] == payload.segment]
        targets = (db.query(models.Student)
                   .filter(models.Student.id.in_(ids or [-1])).all())
    if not targets:
        raise HTTPException(400, "Kimga yuborishni tanlang")

    for s in targets:
        db.add(models.Notification(
            kind=payload.kind or "new_course",
            channel=payload.channel,
            student_id=s.id, phone=s.phone or s.parent_phone,
            title=payload.title,
            body=_fill(payload.body, ism=s.full_name,
                       guruh=s.group.name if s.group else "",
                       kurs=payload.course or ""),
            scheduled_for=date.today(), created_by=user.full_name))
    db.commit()
    return {"created": len(targets)}


# =====================================================================
#  XODIMLARNING SANALARI — tug'ilgan kun va ish yubileyi
#
#  Odam esdan chiqaradi, tizim chiqarmaydi. Sana yaqinlashganda HR'ga
#  vazifa O'ZI paydo bo'ladi — bir necha kun oldindan, ulgurish uchun.
#  Vazifa ichida tayyor tabrik matni ham turadi.
# =====================================================================
def _hr_user(db: Session, branch_id: int | None = None) -> models.User | None:
    """Eslatma kimga tushadi. HR bo'lmasa — asoschiga."""
    q = db.query(models.User).filter(models.User.role == roles.HR_MANAGER,
                                     models.User.is_active == 1)
    if branch_id:
        row = q.filter(models.User.branch_id == branch_id).first()
        if row:
            return row
    return q.first() or (db.query(models.User)
                         .filter(models.User.role == roles.FOUNDER,
                                 models.User.is_active == 1).first())


def _staff_dates(db: Session, user: models.User, *,
                 days: int = roles.STAFF_DATE_HORIZON) -> list:
    """Yaqinlashayotgan tug'ilgan kunlar va ish yubileylari.
    Bugundan boshlab `days` kun ichidagilari, eng yaqini birinchi."""
    today = date.today()
    staff = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 1).all()

    rows = []
    for u in staff:
        for kind, src in (("birthday", u.birth_date),
                          ("anniversary", u.hired_date)):
            nxt = roles.next_occurrence(src, today)
            if not nxt:
                continue
            left = (nxt - today).days
            if left > days:
                continue
            # Yubiley 0 yil bo'lsa — hali bir yil to'lmagan, tabrik erta
            years = nxt.year - src.year
            if kind == "anniversary" and years < 1:
                continue
            rows.append({
                "user_id": u.id,
                "full_name": u.full_name,
                "role_label": roles.UZ_LABELS.get(u.role, u.role),
                "branch": u.branch.name if u.branch else None,
                "phone": u.phone,
                "kind": kind,
                "kind_label": roles.STAFF_DATE_LABELS[kind],
                "tone": roles.STAFF_DATE_TONE[kind],
                "date": nxt.isoformat(),
                "date_label": roles.uz_date(nxt),
                "days_left": left,
                "today": left == 0,
                "soon": left <= roles.STAFF_DATE_LEAD_DAYS,
                "years": years,
                "age": years if kind == "birthday" else None,
                "tenure": roles.tenure_text(u.hired_date, today),
                "source_date": src.isoformat(),
            })
    rows.sort(key=lambda r: r["days_left"])
    return rows


def _staff_date_task(db: Session, row: dict) -> models.Task | None:
    """Bitta sana uchun HR vazifasi. Takror yaratilmaydi: sarlavha
    ichida yil turadi, shuning uchun har yili bir marta chiqadi."""
    on = date.fromisoformat(row["date"])
    if row["kind"] == "birthday":
        title = (f"Tug'ilgan kun: {row['full_name']} — "
                 f"{row['date_label']} ({on.year})")
        greet = (f"{row['full_name']}, tug'ilgan kuningiz muborak bo'lsin! "
                 "Jony Academy jamoasi sizga sog'lik, tinchlik va katta "
                 "yutuqlar tilaydi.")
        body = (f"Xodim: {row['full_name']} ({row['role_label']})\n"
                f"Filial: {row['branch'] or '—'}\n"
                f"Sana: {row['date_label']}\n"
                f"Yoshi: {row['years']} ga to'ladi\n"
                f"Telefon: {row['phone'] or '—'}\n\n"
                f"Tayyor tabrik:\n{greet}")
    else:
        title = (f"Ish yubileyi: {row['full_name']} — "
                 f"{row['years']} yil ({on.year})")
        greet = (f"{row['full_name']}, jamoamizda {row['years']} yil "
                 "bo'ldingiz! Mehnatingiz va sabringiz uchun rahmat — "
                 "shu muhitni siz ham qurdingiz.")
        body = (f"Xodim: {row['full_name']} ({row['role_label']})\n"
                f"Filial: {row['branch'] or '—'}\n"
                f"Ishga kirgan: {row['source_date']}\n"
                f"Necha yil bo'ladi: {row['years']}\n"
                f"Telefon: {row['phone'] or '—'}\n\n"
                f"Tayyor tabrik:\n{greet}")

    exists = (db.query(models.Task)
              .filter(models.Task.title == title).first())
    if exists:
        return None                 # allaqachon bor — takror chiqmaydi

    u = db.query(models.User).get(row["user_id"])
    assignee = _hr_user(db, u.branch_id if u else None)
    t = models.Task(
        title=title,
        description=body,
        assignee_id=assignee.id if assignee else None,
        branch_id=u.branch_id if u else None,
        deadline=on,
        priority="normal",
        source="manual",
        created_by="Tizim",
    )
    db.add(t)
    db.flush()
    _ensure_public_id(db, "task", t)
    return t


def _ensure_staff_date_tasks(db: Session, user: models.User) -> int:
    """AVTOMAT: bir necha kun qolgan sanalar uchun vazifa yaratadi.
    Hech kim tugma bosmaydi — ro'yxat ochilgan zahoti ishlaydi."""
    made = 0
    for row in _staff_dates(db, user, days=roles.STAFF_DATE_LEAD_DAYS):
        if _staff_date_task(db, row) is not None:
            made += 1
    db.commit()
    return made


@app.get("/api/hr/dates")
def hr_dates(
    days: int = roles.STAFF_DATE_HORIZON,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_DATES_ACCESS)),
):
    """Yaqinlashayotgan tug'ilgan kunlar va ish yubileylari.
    Ochilgan zahoti yaqin sanalar uchun vazifa ham yaratiladi."""
    _ensure_staff_date_tasks(db, user)
    rows = _staff_dates(db, user, days=max(1, min(days, 366)))

    staff = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 1).all()
    no_birth = [u.full_name for u in staff if not u.birth_date]
    no_hired = [u.full_name for u in staff if not u.hired_date]

    return {
        "rows": rows,
        "soon": [r for r in rows if r["soon"]],
        "lead_days": roles.STAFF_DATE_LEAD_DAYS,
        "days": days,
        "birthdays": sum(1 for r in rows if r["kind"] == "birthday"),
        "anniversaries": sum(1 for r in rows if r["kind"] == "anniversary"),
        "missing_birth_date": no_birth,
        "missing_hired_date": no_hired,
        "kinds": [{"key": k, "label": lbl, "tone": t}
                  for k, lbl, t in roles.STAFF_DATE_KINDS],
        "hint": (f"Sanaga {roles.STAFF_DATE_LEAD_DAYS} kun qolganda "
                 "HR'ga vazifa avtomat tushadi — tayyor tabrik matni "
                 "bilan. Sana kiritilmagan xodimning tug'ilgan kuni "
                 "eslatilmaydi."),
    }


# =====================================================================
#  REFERRAL TIZIMI
#  "Do'stingni olib kel va chegirma ol"
#
#  Chegirma AVTOMAT beriladi: do'sti to'lov qilgan zahoti olib
#  kelganning chegirmasi paydo bo'ladi. Faqat ro'yxatdan o'tib keyin
#  ketib qolgan odam uchun chegirma berilmaydi.
# =====================================================================
@app.post("/api/referrals")
def add_referral(
    payload: schemas.ReferralCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    """Kim kimni olib kelganini yozadi. Chegirma keyin — do'sti
    to'lov qilganda — avtomat beriladi."""
    friend = db.query(models.Student).get(payload.student_id)
    inviter = db.query(models.Student).get(payload.referrer_student_id)
    if not friend or not inviter:
        raise HTTPException(404, "O'quvchi topilmadi")
    if friend.id == inviter.id:
        raise HTTPException(400, "O'zini o'zi olib kela olmaydi")

    exists = (db.query(models.Discount)
              .filter(models.Discount.kind == "referral",
                      models.Discount.student_id == inviter.id,
                      models.Discount.referrer_student_id == friend.id)
              .first())
    if exists:
        raise HTTPException(400, "Bu referral allaqachon yozilgan")

    # Do'sti allaqachon to'lov qilganmi
    paid = (db.query(func.sum(models.Payment.amount))
            .filter(models.Payment.student_id == friend.id,
                    models.Payment.kind == "payment").scalar() or 0)

    d = models.Discount(
        student_id=inviter.id,
        kind="referral",
        percent=roles.REFERRAL_PERCENT,
        reason=f"{friend.full_name} ni olib keldi",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30 * roles.REFERRAL_MONTHS),
        referrer_student_id=friend.id,
        requested_by=user.full_name,
        status="active" if paid >= roles.REFERRAL_MIN_PAYMENT else "pending",
    )
    if d.status == "active":
        d.approved_by = "Tizim (do'sti to'lov qildi)"
        d.approved_at = datetime.utcnow()
    db.add(d); db.commit(); db.refresh(d)
    return {
        "id": d.id,
        "status": d.status,
        "message": ("Chegirma darrov berildi — do'sti allaqachon to'lagan"
                    if d.status == "active"
                    else "Do'sti to'lov qilgach chegirma avtomat beriladi"),
    }


def _activate_referrals(db: Session, student_id: int) -> int:
    """AVTOMAT: bu o'quvchi to'lov qilgan bo'lsa, uni olib kelgan
    odamning chegirmasini yoqadi."""
    rows = (db.query(models.Discount)
            .filter(models.Discount.kind == "referral",
                    models.Discount.referrer_student_id == student_id,
                    models.Discount.status == "pending").all())
    n = 0
    for d in rows:
        d.status = "active"
        d.approved_by = "Tizim (do'sti to'lov qildi)"
        d.approved_at = datetime.utcnow()
        n += 1
    return n


@app.get("/api/referrals")
def referral_report(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    """Referral dasturi qancha ishlayapti: kim ko'p olib kelgan,
    qancha chegirma berildi va bu qancha pul keltirdi."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    rows = (db.query(models.Discount)
            .filter(models.Discount.kind == "referral",
                    models.Discount.created_at >= datetime.combine(
                        start, datetime.min.time())).all())
    students = {s.id: s for s in db.query(models.Student).all()}
    paid = _student_payments(db)

    by_inviter = {}
    for d in rows:
        inv = students.get(d.student_id)
        fr = students.get(d.referrer_student_id) if d.referrer_student_id else None
        if not inv:
            continue
        r = by_inviter.setdefault(inv.id, {
            "student_id": inv.id, "full_name": inv.full_name,
            "invited": 0, "active": 0, "friends": [],
            "revenue_brought": 0.0, "discount_given": 0.0,
        })
        r["invited"] += 1
        if d.status == "active":
            r["active"] += 1
            fee = inv.group.monthly_fee if inv.group else 0
            r["discount_given"] += (fee or 0) * (d.percent or 0) / 100
        if fr:
            r["friends"].append({
                "id": fr.id, "name": fr.full_name,
                "status": fr.status,
                "paid": round(paid.get(fr.id, {}).get("total", 0.0), 2),
            })
            r["revenue_brought"] += paid.get(fr.id, {}).get("total", 0.0)

    out = sorted(by_inviter.values(), key=lambda r: -r["revenue_brought"])
    for r in out:
        r["revenue_brought"] = round(r["revenue_brought"], 2)
        r["discount_given"] = round(r["discount_given"], 2)
        r["net"] = round(r["revenue_brought"] - r["discount_given"], 2)

    total_rev = sum(r["revenue_brought"] for r in out)
    total_disc = sum(r["discount_given"] for r in out)
    return {
        "months": months,
        "rows": out,
        "inviters": len(out),
        "invited": sum(r["invited"] for r in out),
        "active": sum(r["active"] for r in out),
        "pending": sum(1 for d in rows if d.status == "pending"),
        "revenue": round(total_rev, 2),
        "discount": round(total_disc, 2),
        "net": round(total_rev - total_disc, 2),
        "percent": roles.REFERRAL_PERCENT,
        "months_valid": roles.REFERRAL_MONTHS,
        "hint": (f"Do'stini olib kelgan o'quvchi {roles.REFERRAL_PERCENT}% "
                 f"chegirma oladi. Chegirma do'sti TO'LOV QILGANDA "
                 f"avtomat yoqiladi — shunchaki ro'yxatdan o'tgani "
                 f"yetarli emas."),
    }


# =====================================================================
#  COIN DO'KONI — O'QUVCHINING O'Z KABINETI
#
#  O'quvchi kirganda coin balansini ko'radi va sovg'a tanlaydi.
#  Sovg'a qo'lma-qo'l beriladi, shuning uchun ikki bosqich:
#  SO'RALDI -> BERILDI. So'ralgan paytda coin BAND qilinadi — aks
#  holda bitta coinni ikki marta sarflash mumkin bo'lib qolardi.
# =====================================================================
def _student_of_user(db: Session, user: models.User) -> models.Student | None:
    """Foydalanuvchi hisobiga bog'langan o'quvchi.

    Avval to'g'ridan-to'g'ri bog'lanish, keyin ism bo'yicha — eski
    hisoblarda bog'lanish yo'q bo'lishi mumkin."""
    s = (db.query(models.Student)
         .filter(models.Student.user_id == user.id).first())
    if s:
        return s
    s = (db.query(models.Student)
         .filter(models.Student.full_name == user.full_name).first())
    if s and not s.user_id:
        # Topilgan bo'lsa bog'lab qo'yamiz - keyingi safar tez topiladi
        s.user_id = user.id
        db.commit()
    return s


def _held_coins(db: Session, student_id: int) -> int:
    """So'ralgan, lekin hali berilmagan sovg'alarga band qilingan coin."""
    rows = (db.query(models.RewardRedemption)
            .filter(models.RewardRedemption.student_id == student_id,
                    models.RewardRedemption.status == "requested").all())
    return sum(r.coins or 0 for r in rows)


def _reward_out(r: models.Reward, balance: int = None) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "cost": r.cost,
        "category": r.category or "special",
        "category_label": roles.REWARD_CATEGORY_LABELS.get(
            r.category or "special", "Sovg'a"),
        "tone": roles.REWARD_CATEGORY_TONE.get(r.category or "special", "slate"),
        "stock": r.stock,
        "in_stock": r.stock is None or r.stock > 0,
        "active": bool(r.active),
        # O'quvchiga: yetadimi va yetmasa qancha kam
        "affordable": (balance is not None and balance >= r.cost),
        "need_more": (max(0, r.cost - balance) if balance is not None else None),
    }


@app.get("/api/me/coins")
def my_coins(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """O'quvchining o'z kabineti: coin balansi, qanday yig'ilgani va
    shu coinga olish mumkin bo'lgan sovg'alar."""
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(
            404, "Sizga bog'langan o'quvchi yozuvi topilmadi. "
                 "Administratorga murojaat qiling.")

    earned = int(db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
                 .filter(models.CoinEntry.student_id == s.id,
                         models.CoinEntry.amount > 0).scalar() or 0)
    spent = abs(int(db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
                    .filter(models.CoinEntry.student_id == s.id,
                            models.CoinEntry.amount < 0).scalar() or 0))
    balance = earned - spent
    held = _held_coins(db, s.id)
    available = balance - held

    entries = (db.query(models.CoinEntry)
               .filter(models.CoinEntry.student_id == s.id)
               .order_by(models.CoinEntry.created_at.desc()).limit(50).all())

    rewards = (db.query(models.Reward)
               .filter(models.Reward.active == 1)
               .order_by(models.Reward.cost).all())

    my_orders = (db.query(models.RewardRedemption)
                 .filter(models.RewardRedemption.student_id == s.id)
                 .order_by(models.RewardRedemption.created_at.desc()).all())

    # Keyingi maqsad: hozirgi balansdan qimmatroq eng arzon sovg'a
    next_goal = next((r for r in rewards if r.cost > available), None)

    return {
        "student_id": s.id,
        "full_name": s.full_name,
        "group": s.group.name if s.group else None,
        "balance": balance,
        "earned": earned,
        "spent": spent,
        "held": held,
        "available": available,
        "next_goal": (_reward_out(next_goal, available) if next_goal else None),
        "history": [{
            "id": e.id,
            "amount": e.amount,
            "source": e.source,
            "source_label": roles.COIN_SOURCE_LABELS.get(e.source, e.source),
            "note": e.note,
            "date": e.created_at.date().isoformat() if e.created_at else None,
        } for e in entries],
        "categories": [{"key": k, "label": lbl, "tone": t}
                       for k, lbl, t in roles.REWARD_CATEGORIES],
        "rewards": [_reward_out(r, available) for r in rewards],
        "orders": [{
            "id": o.id,
            "reward": o.reward.name if o.reward else "—",
            "coins": o.coins,
            "status": o.status or "given",
            "status_label": roles.REDEEM_STATUS_LABELS.get(
                o.status or "given", o.status),
            "tone": roles.REDEEM_STATUS_TONE.get(o.status or "given", "slate"),
            "date": o.created_at.date().isoformat() if o.created_at else None,
            "given_at": o.given_at.date().isoformat() if o.given_at else None,
            "note": o.note,
        } for o in my_orders],
    }


@app.post("/api/me/rewards/{reward_id}")
def request_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """O'quvchi sovg'ani o'zi tanlaydi. Coin darrov BAND qilinadi,
    lekin sovg'a qo'lga berilganda hisobdan yechiladi."""
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(404, "Sizga bog'langan o'quvchi yozuvi yo'q")

    r = db.query(models.Reward).get(reward_id)
    if not r or not r.active:
        raise HTTPException(404, "Sovg'a topilmadi")
    if r.stock is not None and r.stock <= 0:
        raise HTTPException(400, "Bu sovg'a tugagan")

    balance = _student_coin_balance(db, s.id)
    available = balance - _held_coins(db, s.id)
    if available < r.cost:
        raise HTTPException(
            400,
            f"Coin yetarli emas. Sizda {available} coin bor, "
            f"\"{r.name}\" uchun {r.cost} coin kerak — "
            f"yana {r.cost - available} coin yig'ish kerak.")

    red = models.RewardRedemption(
        student_id=s.id, reward_id=r.id, coins=r.cost,
        status="requested", requested_by_student=1,
        created_by=user.full_name)
    db.add(red); db.commit(); db.refresh(red)
    return {
        "id": red.id,
        "status": "requested",
        "message": (f"\"{r.name}\" so'raldi. {r.cost} coin band qilindi — "
                    f"sovg'ani markazdan olib ketishingiz mumkin."),
        "available": available - r.cost,
    }


@app.delete("/api/me/rewards/{redemption_id}")
def cancel_my_request(
    redemption_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """O'quvchi o'z so'rovini bekor qiladi — coin qaytadi."""
    s = _student_of_user(db, user)
    red = db.query(models.RewardRedemption).get(redemption_id)
    if not red or not s or red.student_id != s.id:
        raise HTTPException(404, "So'rov topilmadi")
    if red.status != "requested":
        raise HTTPException(400, "Bu sovg'a allaqachon berilgan")
    db.delete(red); db.commit()
    return {"ok": True}


@app.get("/api/rewards/requests")
def reward_requests(
    status_filter: str = "requested",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.REWARD_GIVE)),
):
    """O'quvchilar so'ragan sovg'alar — kimga nima berish kerak."""
    q = db.query(models.RewardRedemption)
    if status_filter:
        q = q.filter(models.RewardRedemption.status == status_filter)
    rows = q.order_by(models.RewardRedemption.created_at).all()

    allowed = {x.id for x in scope_to_branch(
        db.query(models.Student), models.Student, user).all()}
    rows = [r for r in rows if r.student_id in allowed]

    return {
        "rows": [{
            "id": r.id,
            "student_id": r.student_id,
            "student": r.student.full_name if r.student else "—",
            "group": (r.student.group.name
                      if r.student and r.student.group else None),
            "reward": r.reward.name if r.reward else "—",
            "coins": r.coins,
            "status": r.status or "given",
            "status_label": roles.REDEEM_STATUS_LABELS.get(
                r.status or "given", r.status),
            "tone": roles.REDEEM_STATUS_TONE.get(r.status or "given", "slate"),
            "by_student": bool(r.requested_by_student),
            "date": r.created_at.date().isoformat() if r.created_at else None,
            "given_by": r.given_by,
        } for r in rows],
        "count": len(rows),
        "statuses": [{"key": k, "label": lbl, "tone": t}
                     for k, lbl, t in roles.REDEEM_STATUSES],
    }


@app.post("/api/rewards/requests/{rid}/give")
def give_reward(
    rid: int,
    payload: schemas.RewardDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.REWARD_GIVE)),
):
    """Sovg'ani qo'lga berish yoki rad etish.

    BERILDI — coin hisobdan yechiladi (shu paytgacha faqat band edi).
    RAD ETILDI — coin qaytadi."""
    red = db.query(models.RewardRedemption).get(rid)
    if not red:
        raise HTTPException(404, "So'rov topilmadi")
    if red.status != "requested":
        raise HTTPException(400, "Bu so'rov allaqachon hal qilingan")

    r = db.query(models.Reward).get(red.reward_id)
    s = db.query(models.Student).get(red.student_id)

    if not payload.give:
        red.status = "rejected"
        red.note = payload.note
        red.given_by = user.full_name
        red.given_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "status": "rejected"}

    # Berilganda coin yechiladi
    balance = _student_coin_balance(db, red.student_id)
    if balance < red.coins:
        raise HTTPException(
            400, f"Coin yetmayapti: balans {balance}, kerak {red.coins}")

    db.add(models.CoinEntry(
        student_id=red.student_id, amount=-red.coins, source="reward",
        ref_id=red.id, note=r.name if r else "Sovg'a",
        created_by=user.full_name))
    red.status = "given"
    red.given_by = user.full_name
    red.given_at = datetime.utcnow()
    red.note = payload.note
    if r and r.stock is not None:
        r.stock -= 1
    db.commit()

    audit.log(db, user, entity="reward", action="update", entity_id=red.id,
              entity_label=s.full_name if s else "—",
              field="Sovg'a berildi",
              new_value=f"{r.name if r else ''} ({red.coins} coin)",
              branch_id=s.branch_id if s else None, commit=True)
    return {"ok": True, "status": "given",
            "balance": _student_coin_balance(db, red.student_id)}


@app.post("/api/students/{student_id}/link-account")
def link_student_account(
    student_id: int,
    payload: schemas.LinkAccount,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.USER_ADMIN)),
):
    """O'quvchiga kirish hisobi ochish. Shundan keyin u kirib coin
    balansini ko'radi va sovg'a so'ray oladi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if db.query(models.User).filter(
            models.User.username == payload.username).first():
        raise HTTPException(400, "Bu login band")

    u = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=s.full_name,
        role=roles.STUDENT,
        branch_id=s.branch_id,
    )
    db.add(u); db.commit(); db.refresh(u)
    s.user_id = u.id
    db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Kirish hisobi", new_value=payload.username, commit=True)
    return {"user_id": u.id, "username": u.username}


# =====================================================================
#  GAMIFICATION: XP, LEVEL, LIGA, SEASON
#
#  Asosiy qoida: XP balansi ustunni o'zgartirish orqali emas, APPEND-ONLY
#  jurnal orqali yuritiladi. Xato yozuvni o'chirmaymiz — manfiy reversal
#  yozamiz. Shunda "nima bo'lgani" har doim ko'rinib turadi.
#
#  Coin va XP aralashmaydi: XP sarflanmaydi va jarima uchun
#  kamaytirilmaydi; coin esa sovg'aga sarflanadi.
# =====================================================================
def _seed_gamification(db: Session) -> None:
    """Ligalar va qoidalar bazaga bir marta tushadi. Admin o'zgartirsa
    — qayta yozilmaydi, faqat YETISHMAYOTGANI qo'shiladi."""
    have = {r.key for r in db.query(models.XpLeague).all()}
    added = False
    for rank, key, name, lo, hi, color, icon, coin in roles.XP_LEAGUES:
        if key in have:
            continue
        db.add(models.XpLeague(
            key=key, name=name, rank=rank, minimum_xp=lo, maximum_xp=hi,
            color=color, icon=icon, reward_coin=coin, is_active=1))
        added = True
    if added:
        db.commit()

    have = {r.event_code for r in db.query(models.XpRule).all()}
    added = False
    for (code, name, cat, xp, coin, per_lesson, per_day, per_week,
         per_month, mode, approval) in roles.XP_RULES:
        if code in have:
            continue
        db.add(models.XpRule(
            event_code=code, name=name, category=cat, default_xp=xp,
            default_coin=coin, maximum_per_lesson=per_lesson,
            maximum_per_day=per_day, maximum_per_week=per_week,
            maximum_per_month=per_month, mode=mode,
            requires_approval=1 if approval else 0, is_active=1))
        added = True
    if added:
        db.commit()


def _active_season(db: Session) -> models.XpSeason | None:
    today = date.today()
    return (db.query(models.XpSeason)
            .filter(models.XpSeason.is_active == 1,
                    models.XpSeason.start_date <= today)
            .filter((models.XpSeason.end_date.is_(None))
                    | (models.XpSeason.end_date >= today))
            .order_by(models.XpSeason.start_date.desc()).first())


def _leagues(db: Session) -> list:
    return (db.query(models.XpLeague)
            .filter(models.XpLeague.is_active == 1)
            .order_by(models.XpLeague.rank).all())


def _league_for(db: Session, xp: float) -> models.XpLeague | None:
    """Lifetime XP qaysi ligaga to'g'ri keladi."""
    best = None
    for lg in _leagues(db):
        if xp >= (lg.minimum_xp or 0):
            best = lg
    return best


def _xp_rule(db: Session, code: str) -> models.XpRule | None:
    return (db.query(models.XpRule)
            .filter(models.XpRule.event_code == code).first())


def _period_bounds(kind: str, on: date) -> tuple:
    if kind == "day":
        return on, on
    if kind == "week":
        start = on - timedelta(days=on.weekday())
        return start, start + timedelta(days=6)
    s, e = billing.month_bounds(on.year, on.month)
    return s, e


def _rule_cap_hit(db: Session, student_id: int, rule: models.XpRule,
                  on: date, lesson_id: int | None) -> str | None:
    """Chegara tekshiruvi. Chegaraga yetgan bo'lsa sababi qaytadi."""
    def count(start: date, end: date) -> int:
        return (db.query(models.XpTransaction)
                .filter(models.XpTransaction.student_id == student_id,
                        models.XpTransaction.event_code == rule.event_code,
                        models.XpTransaction.is_reversal == 0,
                        models.XpTransaction.created_at
                        >= datetime.combine(start, datetime.min.time()),
                        models.XpTransaction.created_at
                        <= datetime.combine(end, datetime.max.time()))
                .count())

    if rule.maximum_per_lesson and lesson_id:
        n = (db.query(models.XpTransaction)
             .filter(models.XpTransaction.student_id == student_id,
                     models.XpTransaction.event_code == rule.event_code,
                     models.XpTransaction.lesson_id == lesson_id,
                     models.XpTransaction.is_reversal == 0).count())
        if n >= rule.maximum_per_lesson:
            return f"Bu darsda \"{rule.name}\" allaqachon berilgan"
    for cap, kind, word in ((rule.maximum_per_day, "day", "kunlik"),
                            (rule.maximum_per_week, "week", "haftalik"),
                            (rule.maximum_per_month, "month", "oylik")):
        if not cap:
            continue
        s, e = _period_bounds(kind, on)
        if count(s, e) >= cap:
            return (f"\"{rule.name}\" bo'yicha {word} chegara "
                    f"({cap} marta) to'ldi")
    return None


def _recalc_gamification(db: Session, student_id: int,
                         *, commit: bool = True) -> models.StudentGamification:
    """Jamlanmani JURNALDAN qayta hisoblaydi. Jamlanma buzilsa ham
    haqiqat jurnalda qoladi."""
    season = _active_season(db)
    rows = (db.query(models.XpTransaction)
            .filter(models.XpTransaction.student_id == student_id).all())

    lifetime = sum(r.amount or 0 for r in rows)
    # XP hech qachon manfiy bo'lmaydi: reversal 0 dan pastga tushirsa
    # 0 da qoladi (va admin uchun signal yaratiladi).
    below_zero = lifetime < 0
    lifetime = max(0.0, lifetime)

    season_xp = 0.0
    if season:
        season_xp = max(0.0, sum(r.amount or 0 for r in rows
                                 if r.season_id == season.id))

    by_cat: dict = {}
    for r in rows:
        k = r.category or "academic"
        by_cat[k] = round(by_cat.get(k, 0) + (r.amount or 0), 1)

    g = (db.query(models.StudentGamification)
         .filter(models.StudentGamification.student_id == student_id).first())
    if not g:
        g = models.StudentGamification(student_id=student_id)
        db.add(g)

    g.lifetime_xp = round(lifetime, 1)
    g.season_xp = round(season_xp, 1)
    g.season_id = season.id if season else None
    g.current_level = roles.level_for(lifetime)
    g.by_category = json.dumps(by_cat)
    last = max((r.created_at for r in rows), default=None)
    g.last_xp_at = last

    lg = _league_for(db, lifetime)
    old_id = g.current_league_id
    if lg and lg.id != old_id:
        old = db.query(models.XpLeague).get(old_id) if old_id else None
        # Liga faqat YUQORIGA ko'tariladi
        if not old or (lg.rank or 0) > (old.rank or 0):
            g.current_league_id = lg.id
            db.add(models.StudentLeagueHistory(
                student_id=student_id,
                from_league_id=old.id if old else None,
                to_league_id=lg.id, xp_at_promotion=lifetime,
                reward_coin=lg.reward_coin or 0))
            _league_promotion_effects(db, student_id, old, lg)
        elif old_id is None:
            g.current_league_id = lg.id

    if below_zero:
        _fraud_alert(db, "many_reversals", student_id=student_id,
                     description=("Bekor qilishlar XP'ni 0 dan pastga "
                                  "tushirdi — 0 da qoldirildi"))
    if commit:
        db.commit()
    return g


def _league_promotion_effects(db: Session, student_id: int,
                              old, new) -> None:
    """Ligaga ko'tarilganda: bonus coin (bir marta), xabarnoma va
    yutuq."""
    s = db.query(models.Student).get(student_id)
    if not s:
        return
    # Bonus coin BIR MARTA: shu ligaga avval ko'tarilganmi
    given = (db.query(models.StudentLeagueHistory)
             .filter(models.StudentLeagueHistory.student_id == student_id,
                     models.StudentLeagueHistory.to_league_id == new.id)
             .count())
    if (new.reward_coin or 0) > 0 and given <= 1:
        db.add(models.CoinEntry(
            student_id=student_id, amount=new.reward_coin,
            source="league", note=f"{new.name} ligasiga ko'tarildi",
            created_by="Tizim"))

    ach = (db.query(models.GamificationAchievement)
           .filter(models.GamificationAchievement.key
                   == f"league_{new.key}").first())
    if not ach:
        ach = models.GamificationAchievement(
            key=f"league_{new.key}", name=f"{new.name} ligasi",
            description=f"{new.minimum_xp}+ XP to'plandi",
            icon=new.icon, tone="amber", is_active=1)
        db.add(ach)
        db.flush()
    exists = (db.query(models.StudentAchievement)
              .filter(models.StudentAchievement.student_id == student_id,
                      models.StudentAchievement.achievement_id == ach.id)
              .first())
    if not exists:
        db.add(models.StudentAchievement(
            student_id=student_id, achievement_id=ach.id))

    db.add(models.Notification(
        kind="certificate", channel="telegram", student_id=student_id,
        phone=s.phone or s.parent_phone,
        title="Tabriklaymiz!",
        body=(f"{s.full_name}, siz {new.name} ligasiga ko'tarildingiz!"
              + (f" Sizga {new.reward_coin} coin berildi."
                 if (new.reward_coin or 0) > 0 else "")),
        scheduled_for=date.today(), created_by="Tizim"))


def _fraud_alert(db: Session, alert_type: str, *, student_id=None,
                 user_id=None, transaction_id=None, description="",
                 meta=None) -> None:
    db.add(models.XpFraudAlert(
        alert_type=alert_type,
        severity=roles.FRAUD_SEVERITY.get(alert_type, "LOW"),
        user_id=user_id, student_id=student_id,
        transaction_id=transaction_id,
        description=description or roles.FRAUD_LABELS.get(alert_type,
                                                          alert_type),
        meta=json.dumps(meta) if meta else None, status="open"))


def award_xp(db: Session, *, student_id: int, event_code: str,
             amount: float | None = None, by_user: models.User | None = None,
             reason: str | None = None, lesson_id: int | None = None,
             exam_id: int | None = None, source_type: str | None = None,
             source_id: int | None = None,
             idempotency_key: str | None = None,
             on: date | None = None,
             force: bool = False) -> dict:
    """XP beradi. Bitta joydan o'tadi — shuning uchun chegara, takror
    va jurnal qoidalari hamma yerda bir xil ishlaydi.

    Qaytadi: {"ok", "skipped", "reason", "transaction_id", "amount"}
    """
    on = on or date.today()
    s = db.query(models.Student).get(student_id)
    if not s:
        return {"ok": False, "skipped": True, "reason": "O'quvchi topilmadi"}
    # Faol bo'lmagan o'quvchiga yangi XP berilmaydi
    if s.status in ("archived", "left") and not force:
        return {"ok": False, "skipped": True,
                "reason": "Faol bo'lmagan o'quvchiga XP berilmaydi"}

    rule = _xp_rule(db, event_code)
    if rule and not rule.is_active and not force:
        return {"ok": False, "skipped": True,
                "reason": f"\"{rule.name}\" qoidasi o'chirilgan"}

    value = amount if amount is not None else (rule.default_xp if rule else 0)
    if not value:
        return {"ok": False, "skipped": True, "reason": "XP miqdori nol"}

    # Takror yozuv — idempotentlik kaliti bo'yicha
    if idempotency_key:
        dup = (db.query(models.XpTransaction)
               .filter(models.XpTransaction.idempotency_key
                       == idempotency_key).first())
        if dup:
            return {"ok": False, "skipped": True,
                    "reason": "Bu XP allaqachon berilgan",
                    "transaction_id": dup.id}

    if rule and not force:
        hit = _rule_cap_hit(db, student_id, rule, on, lesson_id)
        if hit:
            return {"ok": False, "skipped": True, "reason": hit}

    season = _active_season(db)
    tx = models.XpTransaction(
        student_id=student_id, amount=float(value),
        category=(rule.category if rule else "academic"),
        event_code=event_code,
        xp_rule_id=rule.id if rule else None,
        source_type=source_type or ("manual" if by_user else "system"),
        source_id=source_id,
        group_id=s.group_id, branch_id=s.branch_id,
        lesson_id=lesson_id, exam_id=exam_id,
        season_id=season.id if season else None,
        awarded_by_user_id=by_user.id if by_user else None,
        reason=reason, idempotency_key=idempotency_key)
    db.add(tx)
    db.flush()

    # Qoidada coin ham bo'lsa — birga beriladi
    if rule and (rule.default_coin or 0) > 0:
        db.add(models.CoinEntry(
            student_id=student_id, amount=rule.default_coin,
            source="xp", note=rule.name,
            created_by=by_user.full_name if by_user else "Tizim"))

    _recalc_gamification(db, student_id, commit=False)
    db.commit()
    return {"ok": True, "skipped": False, "transaction_id": tx.id,
            "amount": float(value),
            "label": rule.name if rule else event_code}


def reverse_xp(db: Session, tx_id: int, *, by_user: models.User,
               reason: str) -> dict:
    """Xato XP'ni qaytaradi. Asl yozuv O'CHIRILMAYDI — manfiy yozuv
    qo'shiladi, shunda tarix to'liq qoladi."""
    tx = db.query(models.XpTransaction).get(tx_id)
    if not tx:
        raise HTTPException(404, "Tranzaksiya topilmadi")
    if tx.is_reversal:
        raise HTTPException(400, "Bekor qilingan yozuvni qayta bekor "
                                 "qilib bo'lmaydi")
    already = (db.query(models.XpTransaction)
               .filter(models.XpTransaction.reversed_transaction_id == tx.id)
               .first())
    if already:
        raise HTTPException(400, "Bu yozuv allaqachon bekor qilingan")

    rev = models.XpTransaction(
        student_id=tx.student_id, amount=-(tx.amount or 0),
        category=tx.category, event_code="REVERSAL",
        source_type="reversal", group_id=tx.group_id,
        branch_id=tx.branch_id, lesson_id=tx.lesson_id,
        exam_id=tx.exam_id, season_id=tx.season_id,
        awarded_by_user_id=by_user.id, reason=reason,
        reversed_transaction_id=tx.id, is_reversal=1)
    db.add(rev)
    db.flush()
    _recalc_gamification(db, tx.student_id, commit=False)
    audit.log(db, by_user, entity="xp", action="update", entity_id=tx.id,
              entity_label=f"{tx.event_code} {tx.amount}",
              note=f"Bekor qilindi: {reason}", branch_id=tx.branch_id)
    db.commit()
    return {"ok": True, "reversal_id": rev.id, "amount": -(tx.amount or 0)}


# ------------------------------------------------- Gamification API ----
def _league_out(lg, count: int = 0) -> dict:
    return {
        "id": lg.id, "key": lg.key, "name": lg.name, "rank": lg.rank,
        "minimum_xp": lg.minimum_xp, "maximum_xp": lg.maximum_xp,
        "color": lg.color, "icon": lg.icon,
        "description": lg.description,
        "reward_coin": lg.reward_coin or 0,
        "is_active": bool(lg.is_active), "students": count,
    }


def _rule_out(r) -> dict:
    return {
        "id": r.id, "event_code": r.event_code, "name": r.name,
        "description": r.description, "category": r.category,
        "category_label": roles.XP_CATEGORY_LABELS.get(r.category,
                                                       r.category),
        "tone": roles.XP_CATEGORY_TONE.get(r.category, "slate"),
        "default_xp": r.default_xp or 0, "default_coin": r.default_coin or 0,
        "maximum_per_lesson": r.maximum_per_lesson,
        "maximum_per_day": r.maximum_per_day,
        "maximum_per_week": r.maximum_per_week,
        "maximum_per_month": r.maximum_per_month,
        "mode": r.mode, "requires_approval": bool(r.requires_approval),
        "allowed_roles": r.allowed_roles,
        "is_active": bool(r.is_active),
    }


def _gam_card(db: Session, s: models.Student) -> dict:
    """O'quvchining gamification kartasi: liga, level, XP va progress."""
    g = (db.query(models.StudentGamification)
         .filter(models.StudentGamification.student_id == s.id).first())
    if not g:
        g = _recalc_gamification(db, s.id)

    lifetime = g.lifetime_xp or 0
    lg = db.query(models.XpLeague).get(g.current_league_id) \
        if g.current_league_id else _league_for(db, lifetime)
    all_lg = _leagues(db)
    nxt = None
    if lg:
        after = [x for x in all_lg if (x.rank or 0) > (lg.rank or 0)]
        nxt = after[0] if after else None

    if nxt:
        lo = lg.minimum_xp or 0
        hi = nxt.minimum_xp or 0
        span = max(1, hi - lo)
        pct = round(min(100.0, max(0.0, (lifetime - lo) / span * 100)), 1)
        to_next = max(0, hi - lifetime)
    else:
        pct, to_next = 100.0, 0

    lvl = roles.level_progress(lifetime)
    by_cat = json.loads(g.by_category) if g.by_category else {}
    season = _active_season(db)

    return {
        "student_id": s.id,
        "full_name": s.full_name,
        "lifetime_xp": round(lifetime, 1),
        "season_xp": round(g.season_xp or 0, 1),
        "season": season.name if season else None,
        "level": lvl["level"],
        "level_percent": lvl["percent"],
        "level_to_next": lvl["to_next"],
        "league": _league_out(lg) if lg else None,
        "next_league": _league_out(nxt) if nxt else None,
        "league_percent": pct,
        "league_to_next": round(to_next, 1),
        "max_league": nxt is None,
        "by_category": [{
            "key": k, "label": roles.XP_CATEGORY_LABELS.get(k, k),
            "tone": roles.XP_CATEGORY_TONE.get(k, "slate"),
            "xp": round(v, 1),
        } for k, v in sorted(by_cat.items(), key=lambda x: -x[1]) if v],
        "coins": _coin_balance(db, s.id),
        "last_xp_at": g.last_xp_at.isoformat() if g.last_xp_at else None,
    }


def _coin_balance(db: Session, student_id: int) -> int:
    return int(db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
               .filter(models.CoinEntry.student_id == student_id).scalar() or 0)


@app.get("/api/gamification/leagues")
def list_leagues(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    _seed_gamification(db)
    counts: dict = {}
    for g in db.query(models.StudentGamification).all():
        if g.current_league_id:
            counts[g.current_league_id] = counts.get(g.current_league_id, 0) + 1
    return {
        "rows": [_league_out(lg, counts.get(lg.id, 0))
                 for lg in db.query(models.XpLeague)
                 .order_by(models.XpLeague.rank).all()],
        "xp_per_level": roles.XP_PER_LEVEL,
        "can_edit": user.role in roles.XP_ADMIN,
    }


@app.put("/api/gamification/leagues/{lid}")
def update_league(
    lid: int,
    payload: schemas.LeagueUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    lg = db.query(models.XpLeague).get(lid)
    if not lg:
        raise HTTPException(404, "Liga topilmadi")
    given = payload.model_dump(exclude_unset=True)
    before = {k: getattr(lg, k) for k in given}
    for k, v in given.items():
        setattr(lg, k, int(v) if k == "is_active" and v is not None else v)
    db.commit()
    audit.log(db, user, entity="league", action="update", entity_id=lg.id,
              entity_label=lg.name, old_value=str(before),
              new_value=str(given), note="Liga o'zgartirildi")

    # Chegara o'zgarsa hamma o'quvchining ligasi qayta hisoblanadi
    touched = 0
    if "minimum_xp" in given or "maximum_xp" in given:
        for g in db.query(models.StudentGamification).all():
            _recalc_gamification(db, g.student_id, commit=False)
            touched += 1
        db.commit()
    return {"ok": True, "recalculated": touched}


@app.get("/api/gamification/rules")
def list_xp_rules(
    category: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    _seed_gamification(db)
    q = db.query(models.XpRule)
    if category:
        q = q.filter(models.XpRule.category == category)
    rows = q.order_by(models.XpRule.category, models.XpRule.id).all()
    return {
        "rows": [_rule_out(r) for r in rows],
        "categories": [{"key": k, "label": lbl, "tone": t}
                       for k, lbl, t in roles.XP_CATEGORIES],
        "quick": roles.TEACHER_QUICK_XP,
        "teacher_week_limit": roles.TEACHER_XP_PER_WEEK,
        "teacher_lesson_limit": roles.TEACHER_XP_PER_LESSON,
        "approval_above": roles.APPROVAL_ABOVE_XP,
        "can_edit": user.role in roles.XP_ADMIN,
    }


@app.put("/api/gamification/rules/{rid}")
def update_xp_rule(
    rid: int,
    payload: schemas.XpRuleUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Qoidani tahrirlash. Qiymat o'zgarsa ESKI tranzaksiyalar
    o'zgarmaydi — ular o'sha paytdagi qiymat bilan yozilgan."""
    r = db.query(models.XpRule).get(rid)
    if not r:
        raise HTTPException(404, "Qoida topilmadi")
    given = payload.model_dump(exclude_unset=True)
    before = {k: getattr(r, k) for k in given}
    for k, v in given.items():
        if k in ("requires_approval", "is_active"):
            v = 1 if v else 0
        setattr(r, k, v)
    db.commit()
    audit.log(db, user, entity="xp_rule", action="update", entity_id=r.id,
              entity_label=r.event_code, old_value=str(before),
              new_value=str(given), note="XP qoidasi o'zgartirildi")
    db.commit()
    return {"ok": True}


@app.get("/api/gamification/seasons")
def list_seasons(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    rows = (db.query(models.XpSeason)
            .order_by(models.XpSeason.start_date.desc()).all())
    cur = _active_season(db)
    return {
        "rows": [{
            "id": s.id, "name": s.name,
            "start_date": s.start_date.isoformat() if s.start_date else None,
            "end_date": s.end_date.isoformat() if s.end_date else None,
            "is_active": bool(s.is_active),
            "current": bool(cur and cur.id == s.id),
            "note": s.note,
        } for s in rows],
        "current": cur.name if cur else None,
        "hint": ("Mavsum XP yangi mavsumda 0 dan boshlanadi. "
                 "Umumiy XP hech qachon reset qilinmaydi."),
        "can_edit": user.role in roles.XP_ADMIN,
    }


@app.post("/api/gamification/seasons")
def create_season(
    payload: schemas.SeasonCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    for s in db.query(models.XpSeason).filter(
            models.XpSeason.is_active == 1).all():
        s.is_active = 0
        if not s.end_date:
            s.end_date = date.today()
    row = models.XpSeason(
        name=payload.name, start_date=payload.start_date or date.today(),
        end_date=payload.end_date, note=payload.note, is_active=1,
        created_by=user.full_name)
    db.add(row)
    db.commit()
    for g in db.query(models.StudentGamification).all():
        _recalc_gamification(db, g.student_id, commit=False)
    db.commit()
    audit.log(db, user, entity="season", action="create", entity_id=row.id,
              entity_label=row.name, note="Yangi mavsum ochildi")
    db.commit()
    return {"ok": True, "id": row.id}


# ---- XP berish ------------------------------------------------------
def _teacher_manual_used(db: Session, student_id: int, by_user_id: int,
                         since: date, lesson_id: int | None = None) -> float:
    q = (db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
         .filter(models.XpTransaction.student_id == student_id,
                 models.XpTransaction.awarded_by_user_id == by_user_id,
                 models.XpTransaction.source_type == "manual",
                 models.XpTransaction.is_reversal == 0,
                 models.XpTransaction.created_at
                 >= datetime.combine(since, datetime.min.time())))
    if lesson_id:
        q = q.filter(models.XpTransaction.lesson_id == lesson_id)
    return float(q.scalar() or 0)


def _can_award(db: Session, user: models.User, student: models.Student,
               rule: models.XpRule, amount: float,
               lesson_id: int | None) -> str | None:
    """Ustoz chegaradan chiqmaganini tekshiradi. Sabab qaytsa — bermaymiz."""
    if user.role in roles.XP_ADMIN:
        return None
    if user.role not in (roles.TEACHER, roles.SUPPORT_TEACHER,
                         roles.HEAD_SUPPORT):
        return None

    # Faqat o'z guruhidagi o'quvchiga
    mine = _teacher_of_user(db, user)
    gids = {g.id for g in db.query(models.Group)
            .filter(models.Group.teacher_id == mine.id).all()} if mine else set()
    if student.group_id not in gids:
        _fraud_alert(db, "foreign_group", student_id=student.id,
                     user_id=user.id,
                     description=(f"{user.full_name} o'ziga biriktirilmagan "
                                  f"guruhga XP berishga urindi"))
        db.commit()
        return "Faqat o'z guruhingizdagi o'quvchiga XP bera olasiz"

    if rule.event_code not in roles.TEACHER_QUICK_XP:
        return "Bu qoidadan XP berish sizga ochiq emas"

    week_start = date.today() - timedelta(days=date.today().weekday())
    used_week = _teacher_manual_used(db, student.id, user.id, week_start)
    if used_week + amount > roles.TEACHER_XP_PER_WEEK:
        return (f"Haftalik chegara: bitta o'quvchiga {roles.TEACHER_XP_PER_WEEK} "
                f"XP (bu hafta {round(used_week)} berilgan)")
    if lesson_id:
        used_lesson = _teacher_manual_used(db, student.id, user.id,
                                           date.today(), lesson_id)
        if used_lesson + amount > roles.TEACHER_XP_PER_LESSON:
            return (f"Bir darsda ko'pi bilan {roles.TEACHER_XP_PER_LESSON} XP "
                    f"berish mumkin (bu darsda {round(used_lesson)} berilgan)")
    return None


@app.post("/api/gamification/award")
def give_xp(
    payload: schemas.XpAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_AWARD)),
):
    """Qo'lda XP berish. Ustoz o'zi miqdor yozolmaydi — faqat mavjud
    qoidadan va chegara doirasida."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rule = _xp_rule(db, payload.event_code)
    if not rule:
        raise HTTPException(400, "Bunday XP qoidasi yo'q")

    # Ustoz miqdorni o'zgartira olmaydi
    amount = rule.default_xp or 0
    if payload.amount is not None and user.role in roles.XP_ADMIN:
        amount = payload.amount

    blocked = _can_award(db, user, s, rule, amount, payload.lesson_id)
    if blocked:
        raise HTTPException(400, blocked)

    # Katta miqdor — tasdiqqa
    if (rule.requires_approval or amount > roles.APPROVAL_ABOVE_XP) \
            and user.role not in roles.FULL_ACCESS:
        if not (payload.reason or "").strip():
            raise HTTPException(400, "Sabab yozing")
        req = models.XpApprovalRequest(
            student_id=s.id, event_code=payload.event_code, amount=amount,
            reason=payload.reason, requested_by=user.id, status="pending")
        db.add(req)
        db.commit()
        return {"ok": True, "pending": True, "request_id": req.id,
                "message": "Tasdiqqa yuborildi"}

    if user.role in roles.XP_ADMIN and not (payload.reason or "").strip() \
            and amount > roles.APPROVAL_ABOVE_XP:
        raise HTTPException(400, "Katta XP uchun sabab yozish shart")

    res = award_xp(db, student_id=s.id, event_code=payload.event_code,
                   amount=amount, by_user=user, reason=payload.reason,
                   lesson_id=payload.lesson_id, source_type="manual")
    if not res.get("ok"):
        raise HTTPException(400, res.get("reason", "XP berilmadi"))

    if amount > roles.APPROVAL_ABOVE_XP:
        _fraud_alert(db, "big_manual", student_id=s.id, user_id=user.id,
                     transaction_id=res["transaction_id"],
                     description=(f"{user.full_name} {amount} XP berdi: "
                                  f"{payload.reason or 'sababsiz'}"))
        db.commit()
    return res


@app.post("/api/gamification/award-bulk")
def give_xp_bulk(
    payload: schemas.XpBulkAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_AWARD)),
):
    """Butun guruhga bir vaqtda XP. Kimga berilgani va kimga
    berilmagani aniq qaytadi."""
    rule = _xp_rule(db, payload.event_code)
    if not rule:
        raise HTTPException(400, "Bunday XP qoidasi yo'q")
    amount = rule.default_xp or 0

    given, skipped = [], []
    for sid in payload.student_ids:
        s = db.query(models.Student).get(sid)
        if not s:
            continue
        blocked = _can_award(db, user, s, rule, amount, payload.lesson_id)
        if blocked:
            skipped.append({"student_id": sid, "full_name": s.full_name,
                            "reason": blocked})
            continue
        res = award_xp(db, student_id=sid, event_code=payload.event_code,
                       amount=amount, by_user=user, reason=payload.reason,
                       lesson_id=payload.lesson_id, source_type="manual")
        if res.get("ok"):
            given.append({"student_id": sid, "full_name": s.full_name})
        else:
            skipped.append({"student_id": sid, "full_name": s.full_name,
                            "reason": res.get("reason", "—")})

    if len(given) >= roles.MASS_AWARD_STUDENTS and amount > 20:
        _fraud_alert(db, "mass_award", user_id=user.id,
                     description=(f"{user.full_name} {len(given)} o'quvchiga "
                                  f"{amount} XP dan berdi"))
        db.commit()
    return {"given": given, "skipped": skipped,
            "total_xp": round(len(given) * amount, 1),
            "rule": rule.name, "amount": amount}


@app.post("/api/gamification/transactions/{tx_id}/reverse")
def reverse_transaction(
    tx_id: int,
    payload: schemas.XpReverse,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Bekor qilish sababini yozing")
    return reverse_xp(db, tx_id, by_user=user, reason=payload.reason)


@app.post("/api/gamification/certificate")
def award_certificate(
    payload: schemas.CertAward,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Sertifikat XP'si. Bir raqamga ikki marta berilmaydi; yangi
    yuqoriroq natijada standart holatda faqat FARQI beriladi."""
    res = _xp_for_certificate(
        db, payload.student_id, kind=payload.kind,
        code=payload.event_code, cert_no=payload.cert_no, by_user=user,
        mode=payload.mode or roles.CERT_MODE_DIFF, reason=payload.reason)
    if not res.get("ok"):
        raise HTTPException(400, res.get("reason", "XP berilmadi"))
    return res


@app.get("/api/gamification/approvals")
def list_approvals(
    status_filter: str = "pending",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    q = db.query(models.XpApprovalRequest)
    if status_filter:
        q = q.filter(models.XpApprovalRequest.status == status_filter)
    rows = q.order_by(models.XpApprovalRequest.created_at.desc()).limit(200).all()
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    return {"rows": [{
        "id": r.id, "student_id": r.student_id,
        "student": r.student.full_name if r.student else None,
        "event_code": r.event_code, "amount": r.amount,
        "reason": r.reason, "status": r.status,
        "requested_by": users.get(r.requested_by),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]}


@app.post("/api/gamification/approvals/{rid}")
def decide_approval(
    rid: int,
    payload: schemas.ApprovalDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    r = db.query(models.XpApprovalRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon hal qilingan")
    r.status = "approved" if payload.approve else "rejected"
    r.decided_by = user.id
    r.decided_at = datetime.utcnow()
    r.decision_note = payload.note
    db.commit()
    if payload.approve:
        res = award_xp(db, student_id=r.student_id, event_code=r.event_code,
                       amount=r.amount, by_user=user, reason=r.reason,
                       source_type="manual")
        return {"ok": True, "awarded": res}
    return {"ok": True, "awarded": None}


# ---- O'quvchi profili va leaderboard --------------------------------
def _xp_history(db: Session, student_id: int, limit: int = 100) -> list:
    rows = (db.query(models.XpTransaction)
            .filter(models.XpTransaction.student_id == student_id)
            .order_by(models.XpTransaction.created_at.desc())
            .limit(limit).all())
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    rules = {r.event_code: r.name for r in db.query(models.XpRule).all()}
    return [{
        "id": t.id,
        "date": t.created_at.isoformat() if t.created_at else None,
        "amount": round(t.amount or 0, 1),
        "event_code": t.event_code,
        "label": (rules.get(t.event_code or "")
                  or ("Bekor qilindi" if t.is_reversal else t.event_code)),
        "category": t.category,
        "category_label": roles.XP_CATEGORY_LABELS.get(t.category or "", "—"),
        "tone": roles.XP_CATEGORY_TONE.get(t.category or "", "slate"),
        "source_type": t.source_type,
        "source_label": roles.XP_SOURCE_LABELS.get(t.source_type or "", "—"),
        "by": users.get(t.awarded_by_user_id) or "Tizim",
        "reason": t.reason,
        "is_reversal": bool(t.is_reversal),
        "lesson_id": t.lesson_id,
        "exam_id": t.exam_id,
    } for t in rows]


def _student_ranks(db: Session, student_id: int) -> dict:
    """Guruh, filial va mavsum kesimidagi o'rin."""
    s = db.query(models.Student).get(student_id)
    if not s:
        return {}
    rows = (db.query(models.StudentGamification,
                     models.Student)
            .join(models.Student,
                  models.Student.id == models.StudentGamification.student_id)
            .all())

    def place(items, key):
        items = sorted(items, key=lambda r: -(getattr(r[0], key) or 0))
        for i, r in enumerate(items, 1):
            if r[1].id == student_id:
                return i, len(items)
        return None, len(items)

    grp = [r for r in rows if r[1].group_id == s.group_id]
    br = [r for r in rows if r[1].branch_id == s.branch_id]
    g_rank, g_n = place(grp, "lifetime_xp")
    b_rank, b_n = place(br, "lifetime_xp")
    s_rank, s_n = place(rows, "season_xp")
    return {
        "group_rank": g_rank, "group_total": g_n,
        "branch_rank": b_rank, "branch_total": b_n,
        "season_rank": s_rank, "season_total": s_n,
    }


def _student_gamification(db: Session, s: models.Student) -> dict:
    card = _gam_card(db, s)
    streaks = (db.query(models.XpStreak)
               .filter(models.XpStreak.student_id == s.id).all())
    today = date.today()
    w_start = today - timedelta(days=today.weekday())
    m_start, _e = billing.month_bounds(today.year, today.month)

    def total_since(d):
        return round(float(
            db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
            .filter(models.XpTransaction.student_id == s.id,
                    models.XpTransaction.created_at
                    >= datetime.combine(d, datetime.min.time()))
            .scalar() or 0), 1)

    hist = (db.query(models.StudentLeagueHistory)
            .filter(models.StudentLeagueHistory.student_id == s.id)
            .order_by(models.StudentLeagueHistory.created_at.desc()).all())
    lgs = {l.id: l for l in db.query(models.XpLeague).all()}

    ach = (db.query(models.StudentAchievement, models.GamificationAchievement)
           .join(models.GamificationAchievement,
                 models.GamificationAchievement.id
                 == models.StudentAchievement.achievement_id)
           .filter(models.StudentAchievement.student_id == s.id)
           .order_by(models.StudentAchievement.created_at.desc()).all())

    card.update({
        "group": s.group.name if s.group else None,
        "branch": s.branch.name if s.branch else None,
        "ranks": _student_ranks(db, s.id),
        "streaks": [{
            "kind": st.kind,
            "label": roles.STREAK_LABELS.get(st.kind, st.kind),
            "tone": roles.STREAK_TONE.get(st.kind, "slate"),
            "current": st.current or 0, "longest": st.longest or 0,
        } for st in streaks],
        "xp_week": total_since(w_start),
        "xp_month": total_since(m_start),
        "history": _xp_history(db, s.id),
        "league_history": [{
            "id": h.id,
            "from": lgs[h.from_league_id].name if h.from_league_id in lgs else None,
            "to": lgs[h.to_league_id].name if h.to_league_id in lgs else None,
            "icon": lgs[h.to_league_id].icon if h.to_league_id in lgs else None,
            "xp": round(h.xp_at_promotion or 0, 1),
            "reward_coin": h.reward_coin or 0,
            "date": h.created_at.isoformat() if h.created_at else None,
        } for h in hist],
        "achievements": [{
            "id": a.id, "key": g.key, "name": g.name,
            "description": g.description, "icon": g.icon,
            "tone": g.tone or "amber",
            "date": a.created_at.isoformat() if a.created_at else None,
        } for a, g in ach],
        "empty_hint": ("Hali XP yig'ilmagan. Birinchi XP darsga "
                       "qatnashish orqali olinadi."),
    })
    return card


@app.get("/api/students/{student_id}/gamification")
def student_gamification(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    mine = _student_of_user(db, user)
    if user.role in (roles.STUDENT, roles.PARENT):
        if not mine or mine.id != s.id:
            raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")
    elif user.role not in roles.XP_VIEW:
        raise HTTPException(403, "Ruxsat yo'q")
    return _student_gamification(db, s)


@app.get("/api/me/gamification")
def my_gamification(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(404, "Sizning o'quvchi kartangiz topilmadi")
    return _student_gamification(db, s)


def _mask_name(full: str) -> str:
    """Ommaviy leaderboardda maxfiylik: Jahongir Z."""
    parts = (full or "").split()
    if len(parts) < 2:
        return full
    return f"{parts[0]} {parts[1][0]}."


@app.get("/api/gamification/leaderboard")
def leaderboard(
    scope: str = "lifetime",
    branch_id: int | None = None,
    group_id: int | None = None,
    league: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Reyting. O'quvchi va ota-ona ismlarni qisqartirilgan ko'radi."""
    today = date.today()
    since = None
    if scope == "week":
        since = today - timedelta(days=today.weekday())
    elif scope == "month":
        since, _e = billing.month_bounds(today.year, today.month)

    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).filter(
        models.Student.status.in_(["active", "trial"])).all()
    if group_id:
        students = [s for s in students if s.group_id == group_id]
    ids = [s.id for s in students]
    if not ids:
        return {"rows": [], "scope": scope, "scopes": [
            {"key": k, "label": lbl} for k, lbl in roles.LEADERBOARD_SCOPES]}

    gam = {g.student_id: g for g in db.query(models.StudentGamification)
           .filter(models.StudentGamification.student_id.in_(ids)).all()}
    lgs = {l.id: l for l in db.query(models.XpLeague).all()}

    period_xp: dict = {}
    if since:
        for t in (db.query(models.XpTransaction)
                  .filter(models.XpTransaction.student_id.in_(ids),
                          models.XpTransaction.created_at
                          >= datetime.combine(since, datetime.min.time()))
                  .all()):
            period_xp[t.student_id] = period_xp.get(t.student_id, 0) + (t.amount or 0)

    by_cat_cache: dict = {}
    rows = []
    for s in students:
        g = gam.get(s.id)
        lg = lgs.get(g.current_league_id) if g and g.current_league_id else None
        if league and (not lg or lg.key != league):
            continue
        if scope == "season":
            xp = g.season_xp if g else 0
        elif since:
            xp = period_xp.get(s.id, 0)
        else:
            xp = g.lifetime_xp if g else 0
        cats = json.loads(g.by_category) if g and g.by_category else {}
        by_cat_cache[s.id] = cats
        rows.append({
            "student_id": s.id,
            "full_name": s.full_name,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "league": lg.name if lg else None,
            "league_icon": lg.icon if lg else None,
            "league_color": lg.color if lg else None,
            "level": g.current_level if g else 1,
            "xp": round(xp or 0, 1),
            "lifetime_xp": round((g.lifetime_xp if g else 0) or 0, 1),
            "academic_xp": round(cats.get("academic", 0), 1),
        })

    # Tie-breaker: XP -> akademik XP -> ismi
    rows.sort(key=lambda r: (-r["xp"], -r["academic_xp"], r["full_name"]))
    rows = rows[:max(1, min(limit, 300))]

    # Oldingi kunning snapshoti bilan solishtiramiz
    prev = {sn.student_id: sn.rank for sn in
            db.query(models.SeasonRankSnapshot)
            .filter(models.SeasonRankSnapshot.scope == scope,
                    models.SeasonRankSnapshot.taken_on < today)
            .order_by(models.SeasonRankSnapshot.taken_on.desc())
            .limit(500).all()}

    public = user.role in (roles.STUDENT, roles.PARENT)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        old = prev.get(r["student_id"])
        r["change"] = (None if old is None else old - i)
        r["is_new"] = old is None
        if public:
            r["full_name"] = _mask_name(r["full_name"])

    # Bugungi snapshotni saqlaymiz - ertaga o'zgarish ko'rinsin
    if not db.query(models.SeasonRankSnapshot).filter(
            models.SeasonRankSnapshot.scope == scope,
            models.SeasonRankSnapshot.taken_on == today).first():
        for r in rows:
            db.add(models.SeasonRankSnapshot(
                scope=scope, student_id=r["student_id"], rank=r["rank"],
                xp=r["xp"], taken_on=today))
        db.commit()

    return {
        "rows": rows, "scope": scope,
        "scopes": [{"key": k, "label": lbl}
                   for k, lbl in roles.LEADERBOARD_SCOPES],
        "leagues": [{"key": l.key, "name": l.name, "icon": l.icon}
                    for l in _leagues(db)],
        "masked": public,
    }


# ---- Admin paneli, fraud va analitika -------------------------------
@app.get("/api/gamification/overview")
def gamification_overview(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    today = date.today()
    w_start = today - timedelta(days=today.weekday())

    def total(since=None, manual=None):
        q = db.query(func.coalesce(func.sum(models.XpTransaction.amount), 0))
        if since:
            q = q.filter(models.XpTransaction.created_at
                         >= datetime.combine(since, datetime.min.time()))
        if manual is not None:
            q = (q.filter(models.XpTransaction.source_type == "manual")
                 if manual else
                 q.filter(models.XpTransaction.source_type != "manual"))
        return round(float(q.scalar() or 0), 1)

    all_tx = db.query(models.XpTransaction).all()
    manual = sum(t.amount or 0 for t in all_tx if t.source_type == "manual")
    auto = sum(t.amount or 0 for t in all_tx if t.source_type != "manual")
    grand = manual + auto

    codes: dict = {}
    for t in all_tx:
        if t.event_code:
            codes[t.event_code] = codes.get(t.event_code, 0) + 1
    top_code = max(codes.items(), key=lambda x: x[1])[0] if codes else None
    rules = {r.event_code: r.name for r in db.query(models.XpRule).all()}

    gam = db.query(models.StudentGamification).all()
    active = [g for g in gam if (g.lifetime_xp or 0) > 0]
    lgs = {l.id: l for l in db.query(models.XpLeague).all()}
    dist: dict = {}
    for g in gam:
        if g.current_league_id in lgs:
            k = lgs[g.current_league_id].name
            dist[k] = dist.get(k, 0) + 1

    # Haftada kamida 1 XP olganlar
    got_week = {t.student_id for t in all_tx
                if t.created_at and t.created_at.date() >= w_start}
    students = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"])).all()
    silent = []
    for s in students:
        last = max((t.created_at for t in all_tx if t.student_id == s.id),
                   default=None)
        if not last or (datetime.utcnow() - last).days >= 14:
            silent.append(s.full_name)

    season = _active_season(db)
    open_alerts = db.query(models.XpFraudAlert).filter(
        models.XpFraudAlert.status == "open").count()

    return {
        "today": total(today),
        "week": total(w_start),
        "total": round(grand, 1),
        "active_students": len(active),
        "avg_per_student": (round(sum(g.lifetime_xp or 0 for g in active)
                                  / len(active), 1) if active else 0),
        "top_event": rules.get(top_code or "", top_code),
        "manual_percent": (round(manual / grand * 100, 1) if grand else 0),
        "auto_percent": (round(auto / grand * 100, 1) if grand else 0),
        "season": season.name if season else None,
        "season_participants": len([g for g in gam if (g.season_xp or 0) > 0]),
        "league_distribution": [{"league": k, "students": v}
                                for k, v in sorted(dist.items(),
                                                   key=lambda x: -x[1])],
        "weekly_active_percent": (round(len(got_week) / len(students) * 100, 1)
                                  if students else 0),
        "silent_14d": len(silent),
        "silent_names": silent[:15],
        "open_alerts": open_alerts,
    }


@app.get("/api/gamification/transactions")
def list_transactions(
    student_id: int | None = None,
    event_code: str | None = None,
    source_type: str | None = None,
    branch_id: int | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_VIEW)),
):
    q = db.query(models.XpTransaction)
    if student_id:
        q = q.filter(models.XpTransaction.student_id == student_id)
    if event_code:
        q = q.filter(models.XpTransaction.event_code == event_code)
    if source_type:
        q = q.filter(models.XpTransaction.source_type == source_type)
    if branch_id:
        q = q.filter(models.XpTransaction.branch_id == branch_id)
    rows = (q.order_by(models.XpTransaction.created_at.desc())
            .limit(max(1, min(limit, 1000))).all())

    names = {s.id: s.full_name for s in db.query(models.Student).all()}
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    rules = {r.event_code: r.name for r in db.query(models.XpRule).all()}
    return {"rows": [{
        "id": t.id, "student_id": t.student_id,
        "student": names.get(t.student_id),
        "amount": round(t.amount or 0, 1),
        "event_code": t.event_code,
        "label": rules.get(t.event_code or "",
                           "Bekor qilindi" if t.is_reversal else t.event_code),
        "category": t.category,
        "category_label": roles.XP_CATEGORY_LABELS.get(t.category or "", "—"),
        "source_type": t.source_type,
        "source_label": roles.XP_SOURCE_LABELS.get(t.source_type or "", "—"),
        "by": users.get(t.awarded_by_user_id) or "Tizim",
        "reason": t.reason,
        "is_reversal": bool(t.is_reversal),
        "reversed_id": t.reversed_transaction_id,
        "date": t.created_at.isoformat() if t.created_at else None,
    } for t in rows],
        "can_reverse": user.role in roles.XP_ADMIN}


@app.post("/api/gamification/recalculate")
def recalculate_all(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    """Jamlanmani jurnaldan qayta hisoblaydi. Jurnal — haqiqat manbai,
    shuning uchun bu amal hech qachon ma'lumot yo'qotmaydi."""
    ids = {t.student_id for t in db.query(models.XpTransaction).all()}
    for sid in ids:
        _recalc_gamification(db, sid, commit=False)
    db.commit()
    audit.log(db, user, entity="xp", action="update",
              note=f"{len(ids)} o'quvchining XP jamlanmasi qayta hisoblandi")
    db.commit()
    return {"ok": True, "students": len(ids)}


@app.get("/api/gamification/fraud")
def list_fraud(
    status_filter: str = "open",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    q = db.query(models.XpFraudAlert)
    if status_filter:
        q = q.filter(models.XpFraudAlert.status == status_filter)
    rows = q.order_by(models.XpFraudAlert.created_at.desc()).limit(200).all()
    names = {s.id: s.full_name for s in db.query(models.Student).all()}
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    counts: dict = {}
    for a in db.query(models.XpFraudAlert).all():
        counts[a.status] = counts.get(a.status, 0) + 1
    return {"rows": [{
        "id": a.id, "alert_type": a.alert_type,
        "label": roles.FRAUD_LABELS.get(a.alert_type, a.alert_type),
        "severity": a.severity,
        "tone": roles.FRAUD_TONE.get(a.severity, "slate"),
        "student": names.get(a.student_id),
        "user": users.get(a.user_id),
        "description": a.description, "status": a.status,
        "transaction_id": a.transaction_id,
        "date": a.created_at.isoformat() if a.created_at else None,
    } for a in rows],
        "counts": counts,
        "statuses": [{"key": k, "label": lbl}
                     for k, lbl in roles.FRAUD_STATUSES]}


@app.post("/api/gamification/fraud/{aid}")
def review_fraud(
    aid: int,
    payload: schemas.FraudReview,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN)),
):
    a = db.query(models.XpFraudAlert).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    a.status = payload.status
    a.review_note = payload.note
    a.reviewed_by = user.id
    a.resolved_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.get("/api/gamification/analytics")
def gamification_analytics(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.XP_ADMIN, *roles.FINANCE_ACCESS)),
):
    """CEO uchun: filial, guruh va ustoz kesimida XP, hamda XP bilan
    davomat va natija o'rtasidagi bog'liqlik."""
    gam = {g.student_id: g for g in db.query(models.StudentGamification).all()}
    students = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"])).all()
    groups = {g.id: g for g in db.query(models.Group).all()}
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    teachers = {t.id: t.full_name for t in db.query(models.Teacher).all()}

    def agg(key_fn, label_fn):
        out: dict = {}
        for s in students:
            k = key_fn(s)
            if k is None:
                continue
            row = out.setdefault(k, {"students": 0, "xp": 0.0})
            row["students"] += 1
            row["xp"] += (gam[s.id].lifetime_xp or 0) if s.id in gam else 0
        return sorted([{
            "key": k, "label": label_fn(k),
            "students": v["students"],
            "total_xp": round(v["xp"], 1),
            "avg_xp": round(v["xp"] / v["students"], 1) if v["students"] else 0,
        } for k, v in out.items()], key=lambda r: -r["avg_xp"])

    by_branch = agg(lambda s: s.branch_id, lambda k: branches.get(k, "—"))
    by_group = agg(lambda s: s.group_id,
                   lambda k: groups[k].name if k in groups else "—")
    by_teacher = agg(
        lambda s: groups[s.group_id].teacher_id if s.group_id in groups else None,
        lambda k: teachers.get(k, "—"))

    # XP va davomat bog'liqligi
    pairs = []
    for s in students:
        g = gam.get(s.id)
        if not g:
            continue
        att = (db.query(models.Attendance)
               .filter(models.Attendance.student_id == s.id).all())
        if not att:
            continue
        rate = sum(1 for a in att if a.present) / len(att) * 100
        pairs.append((g.lifetime_xp or 0, rate))
    corr = None
    if len(pairs) >= 3:
        n = len(pairs)
        mx = sum(p[0] for p in pairs) / n
        my = sum(p[1] for p in pairs) / n
        num = sum((p[0] - mx) * (p[1] - my) for p in pairs)
        dx = sum((p[0] - mx) ** 2 for p in pairs) ** 0.5
        dy = sum((p[1] - my) ** 2 for p in pairs) ** 0.5
        corr = round(num / (dx * dy), 2) if dx and dy else None

    # Ustozlar qancha qo'lda XP berdi
    manual: dict = {}
    for t in (db.query(models.XpTransaction)
              .filter(models.XpTransaction.source_type == "manual").all()):
        if t.awarded_by_user_id:
            manual[t.awarded_by_user_id] = manual.get(t.awarded_by_user_id, 0) \
                + (t.amount or 0)
    unames = {u.id: u.full_name for u in db.query(models.User).all()}

    return {
        "by_branch": by_branch,
        "by_group": by_group[:20],
        "weakest_groups": by_group[-5:][::-1] if len(by_group) > 5 else [],
        "by_teacher": by_teacher,
        "attendance_correlation": corr,
        "correlation_hint": ("1 ga yaqin bo'lsa — XP ko'p bo'lgan o'quvchi "
                             "darsga ham ko'p keladi."),
        "manual_by_user": sorted([{
            "user": unames.get(k, "—"), "xp": round(v, 1)
        } for k, v in manual.items()], key=lambda r: -r["xp"])[:10],
    }


# Ligalar va XP qoidalari fayl oxirida to'ldiriladi: _seed_gamification
# shu yerda allaqachon aniqlangan bo'ladi. Har safar ishga tushganda
# YETISHMAYOTGANI qo'shiladi, mavjudiga tegilmaydi.
try:
    from sqlalchemy.orm import Session as _GS
    with _GS(engine) as _db:
        _seed_gamification(_db)
except Exception:
    pass


# =====================================================================
#  AVTOMAT XP — dars, test, streak
#
#  Ustoz hech narsa bosmaydi: yoqlama qo'yilsa XP o'zi qo'shiladi,
#  test natijasi kiritilsa XP o'zi hisoblanadi.
# =====================================================================
def _xp_for_attendance(db: Session, lesson: models.Lesson,
                       by_user: models.User | None = None) -> dict:
    """Yoqlama qo'yilganda: kelgani uchun XP va streak."""
    out = {"awarded": 0, "students": 0}
    rows = (db.query(models.Attendance)
            .filter(models.Attendance.lesson_id == lesson.id).all())
    for a in rows:
        if not a.present:
            _break_streak(db, a.student_id, "attendance")
            continue
        r = award_xp(db, student_id=a.student_id,
                     event_code="LESSON_PRESENT", by_user=by_user,
                     lesson_id=lesson.id, source_type="lesson",
                     source_id=lesson.id, on=lesson.date,
                     idempotency_key=f"LESSON_PRESENT:{lesson.id}:{a.student_id}")
        if r.get("ok"):
            out["awarded"] += r["amount"]
            out["students"] += 1
        _bump_streak(db, a.student_id, "attendance", lesson.date,
                     by_user=by_user)
    db.commit()
    return out


def _bump_streak(db: Session, student_id: int, kind: str, on: date,
                 by_user: models.User | None = None) -> int:
    """Ketma-ketlikni oshiradi va bosqich bonusini BIR MARTA beradi."""
    st = (db.query(models.XpStreak)
          .filter(models.XpStreak.student_id == student_id,
                  models.XpStreak.kind == kind).first())
    if not st:
        st = models.XpStreak(student_id=student_id, kind=kind,
                             current=0, longest=0)
        db.add(st)
    if st.last_event_date == on:
        return st.current                # bir kunda ikki marta sanamaymiz
    st.current = (st.current or 0) + 1
    st.longest = max(st.longest or 0, st.current)
    st.last_event_date = on
    db.flush()

    table = (roles.ATTENDANCE_STREAKS if kind == "attendance"
             else roles.HOMEWORK_STREAKS if kind == "homework" else [])
    for need, code in table:
        if st.current != need:
            continue
        seen = (db.query(models.XpStreakMilestone)
                .filter(models.XpStreakMilestone.student_id == student_id,
                        models.XpStreakMilestone.kind == kind,
                        models.XpStreakMilestone.milestone == need).first())
        if seen:
            break
        db.add(models.XpStreakMilestone(
            student_id=student_id, kind=kind, milestone=need))
        award_xp(db, student_id=student_id, event_code=code,
                 by_user=by_user, source_type="streak", on=on,
                 reason=f"Ketma-ket {need} ta",
                 idempotency_key=f"{code}:{student_id}")
        break
    return st.current


def _break_streak(db: Session, student_id: int, kind: str) -> None:
    """Sababsiz qoldirilsa ketma-ketlik uziladi. XP KAMAYTIRILMAYDI —
    shunchaki berilmaydi."""
    st = (db.query(models.XpStreak)
          .filter(models.XpStreak.student_id == student_id,
                  models.XpStreak.kind == kind).first())
    if st and st.current:
        st.current = 0


def _xp_for_exam(db: Session, exam: models.Exam,
                 by_user: models.User | None = None) -> dict:
    """Test natijasidan XP. Bitta natijaga FAQAT BITTA band qoidasi
    ishlaydi: 92% olgan o'quvchiga +5, +10, +20 va +30 birga
    berilmaydi, faqat +30 beriladi."""
    out = {"awarded": 0.0, "students": 0}
    results = (db.query(models.ExamResult)
               .filter(models.ExamResult.exam_id == exam.id).all())

    for r in results:
        if r.absent or r.percent is None:
            continue
        pct = r.percent

        # 1) Natija bandi — eng yuqorisi
        code = None
        for need, c in roles.TEST_XP_BANDS:
            if pct >= need:
                code = c
                break
        if code:
            res = award_xp(db, student_id=r.student_id, event_code=code,
                           by_user=by_user, exam_id=exam.id,
                           source_type="exam", source_id=r.id, on=exam.date,
                           idempotency_key=f"TESTBAND:{exam.id}:{r.student_id}")
            if res.get("ok"):
                out["awarded"] += res["amount"]
                out["students"] += 1

        # 2) O'sish bonusi — oldingi testga nisbatan, ham faqat bittasi
        prev = (db.query(models.ExamResult)
                .join(models.Exam, models.Exam.id == models.ExamResult.exam_id)
                .filter(models.ExamResult.student_id == r.student_id,
                        models.ExamResult.exam_id != exam.id,
                        models.ExamResult.percent.isnot(None),
                        models.Exam.date <= exam.date)
                .order_by(models.Exam.date.desc()).first())
        if prev and prev.percent is not None:
            gain = pct - prev.percent
            gcode = None
            for need, c in roles.TEST_IMPROVEMENT_BANDS:
                if gain >= need:
                    gcode = c
                    break
            if gcode:
                res = award_xp(
                    db, student_id=r.student_id, event_code=gcode,
                    by_user=by_user, exam_id=exam.id, source_type="exam",
                    source_id=r.id, on=exam.date,
                    reason=f"{prev.percent}% dan {pct}% ga",
                    idempotency_key=f"TESTGAIN:{exam.id}:{r.student_id}")
                if res.get("ok"):
                    out["awarded"] += res["amount"]

        # 3) Mock: qatnashgani uchun
        if exam.kind == "mock":
            award_xp(db, student_id=r.student_id,
                     event_code="MOCK_EXAM_PARTICIPATION", by_user=by_user,
                     exam_id=exam.id, source_type="exam", source_id=r.id,
                     on=exam.date,
                     idempotency_key=f"MOCKPART:{exam.id}:{r.student_id}")

        # 4) Ichki yakuniy imtihon
        if exam.kind == "end":
            award_xp(db, student_id=r.student_id,
                     event_code="INTERNAL_EXAM_PASSED", by_user=by_user,
                     exam_id=exam.id, source_type="exam", source_id=r.id,
                     on=exam.date,
                     idempotency_key=f"ENDPASS:{exam.id}:{r.student_id}")
            if pct >= 90:
                award_xp(db, student_id=r.student_id,
                         event_code="INTERNAL_EXAM_EXCELLENT",
                         by_user=by_user, exam_id=exam.id,
                         source_type="exam", source_id=r.id, on=exam.date,
                         idempotency_key=f"ENDEXC:{exam.id}:{r.student_id}")

        # 5) Unit tugatildi
        if exam.kind == "unit" and pct >= 60:
            award_xp(db, student_id=r.student_id,
                     event_code="UNIT_COMPLETED", by_user=by_user,
                     exam_id=exam.id, source_type="exam", source_id=r.id,
                     on=exam.date,
                     reason=f"Unit {exam.unit_no or ''}".strip(),
                     idempotency_key=f"UNIT:{exam.id}:{r.student_id}")

    # 6) Mock uchun Top 3
    if exam.kind == "mock":
        ranked = sorted([r for r in results
                         if not r.absent and r.band is not None],
                        key=lambda r: -(r.band or 0))
        for i, r in enumerate(ranked[:3], 1):
            award_xp(db, student_id=r.student_id,
                     event_code=f"MOCK_EXAM_TOP_{i}", by_user=by_user,
                     exam_id=exam.id, source_type="exam", source_id=r.id,
                     on=exam.date, reason=f"Mock bo'yicha {i}-o'rin",
                     idempotency_key=f"MOCKTOP:{exam.id}:{r.student_id}")

    db.commit()
    return out


def _xp_for_certificate(db: Session, student_id: int, *, kind: str,
                        code: str, cert_no: str | None,
                        by_user: models.User, mode: str = roles.CERT_MODE_DIFF,
                        reason: str | None = None) -> dict:
    """Sertifikat XP'si. Bir sertifikat raqamiga qayta XP berilmaydi.
    Yangi va yuqoriroq natija olinsa — standart holatda faqat FARQI
    beriladi."""
    if cert_no:
        used = (db.query(models.XpTransaction)
                .filter(models.XpTransaction.idempotency_key
                        == f"CERT:{cert_no}").first())
        if used:
            _fraud_alert(db, "cert_reuse", student_id=student_id,
                         user_id=by_user.id, transaction_id=used.id,
                         description=f"Sertifikat raqami qayta ishlatildi: {cert_no}")
            db.commit()
            return {"ok": False, "skipped": True,
                    "reason": "Bu sertifikat raqamiga XP allaqachon berilgan"}

    ladder = roles.CERT_RULES.get(kind, [])
    rule = _xp_rule(db, code)
    if not rule:
        raise HTTPException(400, "Bunday sertifikat qoidasi yo'q")
    value = rule.default_xp or 0

    if mode == roles.CERT_MODE_DIFF and ladder:
        # Shu turdagi eng yuqori oldingi natija
        prev_best = 0
        for old in (db.query(models.XpTransaction)
                    .filter(models.XpTransaction.student_id == student_id,
                            models.XpTransaction.event_code.in_(ladder),
                            models.XpTransaction.is_reversal == 0).all()):
            prev_best = max(prev_best, old.amount or 0)
        if prev_best:
            value = max(0, value - prev_best)
            if value == 0:
                return {"ok": False, "skipped": True,
                        "reason": ("Oldingi sertifikat XP'si bundan yuqori "
                                   "yoki teng — qo'shimcha XP berilmaydi")}

    return award_xp(db, student_id=student_id, event_code=code,
                    amount=value, by_user=by_user,
                    source_type="certificate", reason=reason,
                    idempotency_key=(f"CERT:{cert_no}" if cert_no else None),
                    force=True)
