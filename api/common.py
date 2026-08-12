"""Auto-extracted from main.py during refactor (split-main). Domain: common."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
from datetime import date, datetime, timedelta, time as dtime
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
        "ALTER TABLE attendances ADD COLUMN homework INTEGER",
        # ---- HR moduli ----
        "ALTER TABLE vacancies ADD COLUMN public_id VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN department_id INTEGER",
        "ALTER TABLE vacancies ADD COLUMN position_id INTEGER",
        "ALTER TABLE vacancies ADD COLUMN request_id INTEGER",
        "ALTER TABLE vacancies ADD COLUMN hiring_manager_id INTEGER",
        "ALTER TABLE vacancies ADD COLUMN recruiter_id INTEGER",
        "ALTER TABLE vacancies ADD COLUMN employment_type VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN work_schedule VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN duties TEXT",
        "ALTER TABLE vacancies ADD COLUMN requirements TEXT",
        "ALTER TABLE vacancies ADD COLUMN experience_years FLOAT",
        "ALTER TABLE vacancies ADD COLUMN education VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN language_level VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN certificates VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN probation_months INTEGER",
        "ALTER TABLE vacancies ADD COLUMN kpi_note TEXT",
        "ALTER TABLE vacancies ADD COLUMN priority VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN opened_on DATE",
        "ALTER TABLE vacancies ADD COLUMN target_close DATE",
        "ALTER TABLE vacancies ADD COLUMN close_reason VARCHAR",
        "ALTER TABLE vacancies ADD COLUMN hired_count INTEGER DEFAULT 0",
        "ALTER TABLE teachers ADD COLUMN user_id INTEGER",
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
        "ALTER TABLE payments ADD COLUMN entered_at TIMESTAMP",
        "ALTER TABLE expenses ADD COLUMN staff_user_id INTEGER",
        "ALTER TABLE expenses ADD COLUMN qty FLOAT",
        "ALTER TABLE expenses ADD COLUMN consumable_id INTEGER",
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
        # Daraja keyingi oydan kuchga kirishi uchun
        "ALTER TABLE teachers ADD COLUMN pending_grade VARCHAR",
        "ALTER TABLE teachers ADD COLUMN pending_grade_from DATE",
        # Nomzodni ikki bosqichda sinash
        "ALTER TABLE lesson_observations ADD COLUMN stage VARCHAR DEFAULT 'before'",
        "ALTER TABLE lesson_observations ADD COLUMN attempt INTEGER DEFAULT 1",
        # Lead atributsiyasi: qaysi kontentdan kelgani
        "ALTER TABLE leads ADD COLUMN content_id INTEGER",
        "ALTER TABLE leads ADD COLUMN campaign_id INTEGER",
        "ALTER TABLE leads ADD COLUMN social_message_id INTEGER",
        # Examiner oyligi: kim o'tkazgani + jarima maydonlari
        "ALTER TABLE exams ADD COLUMN examiner_id INTEGER",
        "ALTER TABLE exams ADD COLUMN penalty_lc_up INTEGER DEFAULT 0",
        "ALTER TABLE exams ADD COLUMN penalty_coin INTEGER DEFAULT 0",
        "ALTER TABLE exams ADD COLUMN penalty_delay_hours FLOAT DEFAULT 0",
        "ALTER TABLE exams ADD COLUMN penalty_note TEXT",
        "ALTER TABLE exams ADD COLUMN penalty_by VARCHAR",
        # Muzlatish va lid geo-ma'lumotlari
        "ALTER TABLE students ADD COLUMN address VARCHAR",
        "ALTER TABLE students ADD COLUMN school VARCHAR",
        "ALTER TABLE students ADD COLUMN school_grade VARCHAR",
        "ALTER TABLE students ADD COLUMN frozen_until DATE",
        "ALTER TABLE students ADD COLUMN frozen_note VARCHAR",
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
            # 2026-08-11: Jahongir yangi 14 pog'onali shkala berdi
            # (manfiylari bilan). Bir MARTA eski umumiy qoidalar yangi
            # shkalaga almashtiriladi (marker qator) - keyin asoschi
            # UI'dan o'zgartirsa qayta yozilmaydi.
            _mk = (db.query(models.ExamCoinRule)
                   .filter(models.ExamCoinRule.kind == "__migr_v2__")
                   .first())
            if _mk is None:
                (db.query(models.ExamCoinRule)
                 .filter(models.ExamCoinRule.kind.is_(None))
                 .delete(synchronize_session=False))
                for pct, coins in roles.DEFAULT_EXAM_COIN_RULES:
                    db.add(models.ExamCoinRule(min_percent=pct,
                                               coins=coins))
                db.add(models.ExamCoinRule(
                    min_percent=-999, coins=0, kind="__migr_v2__"))
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

PUBLIC_ID_PREFIX = {
    "student": "STU",
    "parent": "PAR",
    "user": "EMP",
    "lead": "LID",
    "group": "GRP",
    "payment": "PAY",
    "contract": "SHT",
    "task": "TSK",
    "content": "CNT",
    "staff_request": "REQ",
    "vacancy": "VAC",
    "book_order": "BOOK",
    "exam_order": "EXM",
    "application": "ARZ",
    "interview": "SUH",
    "offer": "OFR",
    "leave": "TTL",
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

SCHEMA_STAMP = "stamp_2026_08_04e"

def _schema_bootstrap():
    db = SessionLocal()
    try:
        try:
            done = db.query(models.SchemaMigration).filter(
                models.SchemaMigration.version == SCHEMA_STAMP).first()
        except Exception:
            done = None
        if done:
            return
        _ensure_new_columns()
        _backfill_public_ids()
        migrations.run(db)
        db.add(models.SchemaMigration(version=SCHEMA_STAMP))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()

def student_balance(db: Session, student_id: int) -> float:
    total = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
        .filter(models.Payment.student_id == student_id)
        .scalar()
    )
    return float(total or 0)

def _balances_bulk(db: Session, student_ids) -> dict:
    """Hamma o'quvchi balansi BITTA so'rovda. Avval har o'quvchiga
    alohida so'rov ketardi (1000+ o'quvchida sekinlashadi -
    2026-08-12 tahlilida aniqlangan)."""
    ids = list(student_ids)
    if not ids:
        return {}
    out = {}
    CHUNK = 900
    for i in range(0, len(ids), CHUNK):
        rows = (db.query(models.Payment.student_id,
                         func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.student_id.in_(ids[i:i + CHUNK]))
                .group_by(models.Payment.student_id).all())
        out.update({sid: float(v or 0) for sid, v in rows})
    return out


def _neg_since_bulk(db: Session, student_ids) -> dict:
    """Har qarzdor uchun balans QACHONDAN BERI minusda (aging).

    Jahongir (2026-08-12): "qarzdorlarni 0-15 / 16-30 / 31-60 / 60+
    kun bo'yicha bo'lish". To'lovlar xronologiyasi bo'ylab yurib,
    balans oxirgi marta 0 dan pastga tushgan sana topiladi."""
    ids = list(student_ids)
    if not ids:
        return {}
    out = {}
    CHUNK = 700
    for i in range(0, len(ids), CHUNK):
        rows = (db.query(models.Payment.student_id,
                         models.Payment.amount,
                         models.Payment.created_at)
                .filter(models.Payment.student_id.in_(ids[i:i + CHUNK]))
                .order_by(models.Payment.student_id,
                          models.Payment.created_at,
                          models.Payment.id).all())
        cur, run, since = None, 0.0, None
        for sid, amt, at in rows:
            if sid != cur:
                if cur is not None and run < 0 and since:
                    out[cur] = since
                cur, run, since = sid, 0.0, None
            prev = run
            run += float(amt or 0)
            if run < 0 and prev >= 0:
                since = at.date() if hasattr(at, "date") else at
            elif run >= 0:
                since = None
        if cur is not None and run < 0 and since:
            out[cur] = since
    return out


DEBT_AGING_BUCKETS = [
    ("b15", "0-15 kun", 15),
    ("b30", "16-30 kun", 30),
    ("b60", "31-60 kun", 60),
    ("b60p", "60+ kun", None),
]


def _aging_bucket(days: int) -> str:
    for key, _lbl, lim in DEBT_AGING_BUCKETS:
        if lim is None or days <= lim:
            return key
    return "b60p"


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

def _user_branch_ids(db, user: models.User) -> list:
    """Xodimning BARCHA filiallari (asosiy + qo'shimcha). So'rov soni
    oshmasin deb natija user obyektiga yopishtirib qo'yiladi.

    IKKI MANBADAN yig'iladi:
      1. user_branches — xodim kartasidan (Xodimlar bo'limi);
      2. teacher_branches — USTOZ kartasidan (Ustozlar bo'limi).

    (2) 2026-08-10 da qo'shildi. Muammo: HR ustoz kartasida "ikkinchi
    filial" ni belgilaganda faqat teacher_branches ga yozilardi
    (teachers.py:_sync_teacher_branches), user_branches esa bo'sh
    qolardi. Natijada ustozning KIRISH hisobi hamon bitta filialga
    bog'liq bo'lib, ikkinchi filialdagi o'z guruhini ro'yxatda ko'rib
    tursa ham ocholmasdi ("Bu guruh boshqa filialga tegishli").
    Endi ikkala jadval ham hisobga olinadi — HR qayerdan belgilashidan
    qat'i nazar ishlaydi."""
    cached = getattr(user, "_all_branch_ids", None)
    if cached is not None:
        return cached
    extra = [ub.branch_id for ub in db.query(models.UserBranch)
             .filter(models.UserBranch.user_id == user.id).all()]
    # Ustoz kartasidagi qo'shimcha filiallar
    try:
        t = (db.query(models.Teacher)
             .filter(models.Teacher.user_id == user.id).first())
        if t:
            if t.branch_id:
                extra.append(t.branch_id)
            extra += [tb.branch_id for tb in db.query(models.TeacherBranch)
                      .filter(models.TeacherBranch.teacher_id == t.id).all()]
    except Exception:
        pass
    # SUPPORT TEACHER: uning filiallari BIRIKTIRILGAN GURUHLARIDAN
    # chiqadi (2026-08-10, Jahongir: "supportlarda boshqa filialdagi
    # guruhlari bor, lekin guruhlarida turibdi — guruhga kirsa
    # 'guruh boshqa filialda' degan qizil yozuv chiqayabdi").
    #
    # Supportda ustozdan farqli o'laroq "qo'shimcha filial" degan
    # alohida sozlama YO'Q: unga shunchaki guruh biriktiriladi
    # (SupportAssignment) va o'sha guruh istalgan filialda bo'lishi
    # mumkin. Shuning uchun filiallari biriktirilgan guruhlarining
    # filialidan olinadi — ro'yxatda ko'ringan guruh ochilmay
    # qolmasin.
    try:
        if user.role == roles.SUPPORT_TEACHER:
            extra += [
                b for (b,) in db.query(models.Group.branch_id)
                .join(models.SupportAssignment,
                      models.SupportAssignment.group_id == models.Group.id)
                .filter(models.SupportAssignment.user_id == user.id,
                        models.Group.branch_id.isnot(None))
                .distinct().all()
            ]
    except Exception:
        pass
    ids = ([user.branch_id] if user.branch_id else [])
    for b in extra:
        if b and b not in ids:
            ids.append(b)
    user._all_branch_ids = ids
    return ids

def _ensure_student_account(db, s) -> str | None:
    """O'quvchiga kirish hisobini AVTOMAT ochadi (2026-08-10).

    Jahongir: "o'quvchi kiritildimi avtomat unga o'quvchi maqomi va
    akkaunti ochilsin, nomeri login paroli esa jonyjony bo'lsin."

    Login = telefon raqami (faqat raqamlar), parol = jonyjony.
    Qaytaradi: yaratilgan login yoki None.

    Idempotent — hisobi bor o'quvchiga ikkinchi marta ochmaydi.
    Telefon raqami bo'lmasa yoki band bo'lsa JIMGINA o'tkazib
    yuboriladi: o'quvchi kartasi baribir yaratilishi kerak, hisob
    esa keyin telefon kiritilganda ochiladi (bu funksiya
    tahrirlashda ham chaqiriladi)."""
    from auth import hash_password
    if not s or s.user_id:
        return None
    raw = (s.phone or s.parent_phone or "")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 7:
        return None
    if db.query(models.User).filter(models.User.username == digits).first():
        return None
    try:
        u = models.User(
            username=digits,
            password_hash=hash_password(roles.DEFAULT_PASSWORD),
            full_name=s.full_name,
            role=roles.STUDENT,
            branch_id=s.branch_id,
            is_active=1,
        )
        db.add(u)
        db.flush()
        s.user_id = u.id
        db.commit()
        return digits
    except Exception:
        db.rollback()
        return None


def _branch_in(db, user: models.User, column):
    """RO'YXAT filtri uchun shart: yozuv xodimning FILIALLARIDAN
    birida bo'lsin.

    NEGA (2026-08-10): tizimda o'nlab joyda
    `X.branch_id == user.branch_id` yozilgan edi — ya'ni faqat ASOSIY
    filial. Ikki filialda ishlaydigan xodim ikkinchi filialdagi
    yozuvlarni umuman ko'rmasdi. Eng og'rig'i examinerlarda chiqdi:
    ustoz yuborgan imtihon so'rovi RO'YXATDA ko'rinmasdi (garchi
    qabul qilish huquqi bo'lsa ham) — Jahongir "qabul qilinishi kerak
    bo'lgan imtihonlar ko'rinmayapti" deb xabar berdi.

    Endi hamma joyda BITTA qoida: xodimning barcha filiallari."""
    ids = _user_branch_ids(db, user) or [-1]
    return column.in_(ids)


def _user_roles(db, user: models.User) -> list:
    """Xodimning BARCHA lavozimlari: asosiysi + qo'shimchalari.

    Birinchisi doim asosiy lavozim (User.role) — tanlanmagan holatda
    shu ishlatiladi."""
    cached = getattr(user, "_all_roles", None)
    if cached is not None:
        return cached
    out = [user.role] if user.role else []
    try:
        for ur in (db.query(models.UserRole)
                   .filter(models.UserRole.user_id == user.id).all()):
            if ur.role and ur.role not in out and ur.role in roles.ALL_ROLES:
                out.append(ur.role)
    except Exception:
        pass
    user._all_roles = out
    return out


def _in_user_branches(db, user: models.User, branch_id,
                      null_ok: bool = False) -> bool:
    """Shu filial foydalanuvchiga tegishlimi (asosiy YOKI qo'shimcha).

    NEGA KERAK (2026-08-10, Jahongir xabar berdi): ikki filialda
    ishlaydigan xodim RO'YXATDA ikkala filial yozuvlarini ko'rardi
    (scope_to_branch to'g'ri ishlaydi — u _user_branch_ids ishlatadi),
    LEKIN bittasini OCHMOQCHI bo'lsa 403 "boshqa filialga tegishli"
    chiqardi. Sababi: yakka yozuv tekshiruvlari user.branch_id ni
    (BITTA filial) solishtirardi. Natijada ustoz o'z guruhini ro'yxatda
    ko'rib, ustiga bosganda ochib bo'lmasdi; examiner esa ikkinchi
    filial imtihonini qabul qila olmasdi.

    Endi ro'yxat va yakka yozuv tekshiruvi BIR XIL qoidadan yuradi."""
    if user.role in tuple(roles.ORG_WIDE_ROLES):
        return True
    if not user.branch_id:
        # Filialga umuman bog'lanmagan xodim — cheklov qo'llanmaydi
        return True
    if branch_id is None:
        # DIQQAT: filiali YO'Q yozuv (branch_id = NULL) ataylab
        # RUXSAT ETILMAYDI. Sabab: filialsiz yozuv odatda butun
        # tashkilotga tegishli (masalan filialga bog'lanmagan HR
        # xodimi) — filial rahbari uni tahrirlay olmasligi kerak.
        # Filialsizga ruxsat berilishi kerak bo'lgan kam sonli
        # joyda (masalan hali filial biriktirilmagan o'quvchi)
        # null_ok=True beriladi.
        return bool(null_ok)
    return branch_id in _user_branch_ids(db, user)


def scope_to_branch(query, model, user: models.User, branch_id=None):
    """Filialga bo'yicha cheklash.

    Ikki xil cheklash bor va ular aralashmasligi kerak:
      1) HUQUQ - filialga bog'langan xodim faqat O'Z FILIALLARINI
         (asosiy + qo'shimcha) ko'radi. Buni hech kim aylanib o'tolmaydi.
      2) FILTR - butun tashkilotni ko'radigan odam (asoschi, HR, SMM)
         istagan filialni alohida ko'rmoqchi bo'lsa, branch_id beradi.
    """
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = _user_branch_ids(query.session, user)
        # O'z filiallaridan bittasini tanlab ko'rishi mumkin
        if branch_id and branch_id in allowed:
            return query.filter(model.branch_id == branch_id)
        return query.filter(model.branch_id.in_(allowed or [-1]))
    if branch_id and hasattr(model, "branch_id"):
        return query.filter(model.branch_id == branch_id)
    return query

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

def _ensure_teacher_card(db: Session, u: models.User):
    """O'qituvchi yoki support roli bilan ochilgan hisobga Ustozlar
    bo'limida ham karta ochib qo'yadi — HR dan qo'shilsa ham, ikkala
    tomonda ko'rinib turadi. Ism mos kelgan egasiz karta bo'lsa,
    dublikat ochmasdan o'shanga bog'laydi."""
    if u.role not in (roles.TEACHER, roles.SUPPORT_TEACHER):
        return None
    t = (db.query(models.Teacher)
         .filter(models.Teacher.user_id == u.id).first())
    if t:
        return t
    t = (db.query(models.Teacher)
         .filter(models.Teacher.full_name == u.full_name,
                 models.Teacher.user_id.is_(None)).first())
    if t:
        t.user_id = u.id
        if not t.branch_id:
            t.branch_id = u.branch_id
        return t
    t = models.Teacher(full_name=u.full_name, user_id=u.id,
                       branch_id=u.branch_id, is_active=1,
                       hired_date=u.hired_date or date.today())
    db.add(t)
    return t

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

def _student_coin_balance(db: Session, student_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
        .filter(models.CoinEntry.student_id == student_id)
        .scalar()
    )
    return int(total or 0)

def _group_students(db: Session, group_id: int):
    return (
        db.query(models.Student)
        .filter(models.Student.group_id == group_id)
        .order_by(models.Student.full_name)
        .all()
    )

def _exam_summary(db: Session, exam: models.Exam) -> schemas.ExamOut:
    # O'rtacha FAQAT birinchi urinishdan va faqat hisobga kiradigan
    # (imtihongacha kamida 1 yo'qlamasi bor) o'quvchilardan. Retake
    # va yangi kelganlar o'rtachani o'zgartirmaydi (Jahongir).
    scored = [r for r in exam.results
              if r.percent is not None and not r.absent
              and (r.counted is None or r.counted != 0)]
    return schemas.ExamOut(
        id=exam.id, group_id=exam.group_id, kind=exam.kind,
        unit_no=exam.unit_no, title=exam.title, date=exam.date,
        max_score=exam.max_score, created_by=exam.created_by,
        created_at=exam.created_at,
        result_count=len([r for r in exam.results if not r.absent]),
        avg_percent=round(sum(r.percent for r in scored) / len(scored), 1)
        if scored else None,
    )

def _period_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"

def _shift_month(year: int, month: int, delta: int) -> tuple:
    idx = (year * 12 + (month - 1)) + delta
    return idx // 12, idx % 12 + 1

def _utc_window(start: date, end: date):
    """Mahalliy sana oralig'ini UTC datetime oynasiga aylantiradi.

    created_at UTC'da saqlanadi, hisobot esa Toshkent oyi bo'yicha
    so'raladi. Chegaralar surilmasa, har oyning 1-kuni 00:00-05:00
    orasidagi to'lovlar yangi oy hisobotidan YO'QOLIB, eski oyga
    tushib qolardi — "bugungi tushum"dagi xatoning oylik varianti."""
    off = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    return (datetime.combine(start, datetime.min.time()) - off,
            datetime.combine(end, datetime.max.time()) - off)

def _income_by_method(db: Session, user, start: date, end: date,
                      branch_id=None) -> dict:
    """Bir oraliqdagi haqiqiy tushumni to'lov usuli kesimida qaytaradi."""
    q = db.query(models.Payment).join(models.Student).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= _utc_window(start, end)[0],
        models.Payment.created_at <= _utc_window(start, end)[1],
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(_branch_in(db, user, models.Student.branch_id))
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
        gq = gq.filter(_branch_in(db, user, models.Group.branch_id))
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

def _active_student_count(db: Session, group_id: int,
                          exclude_student_id: int | None = None) -> int:
    """Guruhdagi FAOL o'quvchilar soni — xona/guruh sig'imini
    tekshirishda ishlatiladi.

    Sinovdagi (trial) va muzlatilgan (frozen) o'quvchilar
    HISOBLANMAYDI: muzlatilgan darsga kelmaydi, joy egallamaydi;
    sinovdagi hali tasdiqlanmagan. Bu /api/groups va /api/timetable
    (timetable.py) dagi student_count bilan BIR XIL, ataylab izchil
    qoida — o'sha yerlarda "STATISTIKA FAQAT FAOL O'QUVCHILAR
    BO'YICHA: sinovdagi va muzlatilganlar songa qo'shilmaydi" deb
    aniq yozilgan. Bu funksiya paydo bo'lishidan oldin sig'im
    tekshiruvi xato ravishda `status != "archived"` (ya'ni trial VA
    frozen'ni ham qo'shib) hisoblardi — 34 o'quvchili guruhda 5 tasi
    muzlatilgan bo'lsa ham "34 ta, sig'maydi" derdi, aslida 29 ta
    joy band edi (2026-08-09, Jahongir xabar qildi)."""
    q = db.query(models.Student).filter(
        models.Student.group_id == group_id,
        models.Student.status == "active")
    if exclude_student_id is not None:
        q = q.filter(models.Student.id != exclude_student_id)
    return q.count()

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
        # entry.py bu funksiyani ishga tushgach almashtirishi mumkin
        # (M._check_teacher_load = ...) - bo'linishdan oldin bitta
        # fayl bo'lgani uchun bu avtomat ishlagan, endi main orqali
        # dinamik chaqiramiz, aks holda eski (almashtirilmagan)
        # versiya ishlatilib qolardi.
        import main as _main
        problems += _main._check_teacher_load(db, teacher_id, group_id)

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

    # Xona sig'imi FAOL o'quvchilardan kichik bo'lmasin (sinovdagi
    # va muzlatilganlar hisoblanmaydi — _active_student_count'ga q.)
    if room_id and group_id:
        room = db.query(models.Room).get(room_id)
        n = _active_student_count(db, group_id)
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

    n = _active_student_count(db, g.id, exclude_student_id=s.id)
    rooms = {r.id: r for r in db.query(models.Room).all()}
    cap = _group_capacity(g, rooms)
    if cap and n + 1 > cap:
        problems.append(_problem(
            "over_capacity",
            f"\"{g.name}\" guruhida {n} ta o'quvchi bor, sig'im {cap} ta. "
            f"Yana bittasi sig'maydi."))

    # YOSH CHEGARASI: Kids English kabi kurslarga faqat belgilangan
    # yoshdagi o'quvchilar olinadi. Bu qat'iy qoida (block) — force
    # bilan ham aylanib o'tib bo'lmaydi.
    age_lim = roles.SUBJECT_AGE_LIMITS.get(g.subject or "")
    if age_lim:
        lo, hi = age_lim
        if s.birth_date:
            age = (date.today() - s.birth_date).days / 365.25
            if not (lo <= age <= hi + 0.999):
                problems.append(_problem(
                    "age_limit",
                    f"\"{roles.SUBJECT_LABELS.get(g.subject, g.subject)}\" "
                    f"kursiga faqat {lo}-{hi} yoshdagi o'quvchilar "
                    f"olinadi. {s.full_name} — {int(age)} yoshda."))
        else:
            problems.append(_problem(
                "age_unknown",
                f"Bu kursga {lo}-{hi} yosh chegarasi bor, lekin "
                f"o'quvchining tug'ilgan sanasi kiritilmagan — yoshini "
                "tekshirib bo'lmadi. Avval sanani kiriting."))

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

def _charge_skipped(db: Session, student_id: int, period: str) -> bool:
    """Asoschi o'chirgan avto-oylik qayta yozilmasin."""
    return (db.query(models.ChargeSkip)
            .filter(models.ChargeSkip.student_id == student_id,
                    models.ChargeSkip.period == period)
            .first() is not None)

def _teacher_owns(db: Session, group: models.Group,
                  user: models.User) -> bool:
    """Ustoz shu guruhga tegishlimi: o'z guruhi yoki o'rniga o'tayotgan."""
    t = _teacher_of_user(db, user)
    if not t:
        return False
    if group.teacher_id == t.id:
        return True
    # Support teacher — biriktirilgan guruhiga kiradi
    if user.role == roles.SUPPORT_TEACHER and db.query(
            models.SupportAssignment).filter(
            models.SupportAssignment.user_id == user.id,
            models.SupportAssignment.group_id == group.id).first():
        return True
    # O'rinbosarlik davrida boshqa ustozning guruhi ham ochiladi
    return db.query(models.Substitution).filter(
        models.Substitution.group_id == group.id,
        models.Substitution.substitute_teacher_id == t.id,
        models.Substitution.status.in_(["accepted", "done"])).first() is not None

def _homework_stats(db: Session, student_id: int,
                    since: date | None = None) -> dict:
    """Bitta o'quvchining uy vazifasi holati.

    Bitta joydan o'tadi — shuning uchun risk, ustoz ro'yxati, o'quvchi
    kartasi va bolaning o'z kabineti bir xil raqamni ko'rsatadi."""
    q = (db.query(models.Attendance, models.Lesson)
         .join(models.Lesson,
               models.Attendance.lesson_id == models.Lesson.id)
         .filter(models.Attendance.student_id == student_id,
                 models.Attendance.homework.isnot(None)))
    if since:
        q = q.filter(models.Lesson.date >= since)
    rows = q.all()
    done = sum(1 for a, _ in rows if a.homework == 1)
    partial = sum(1 for a, _ in rows if a.homework == 2)
    missed = sum(1 for a, _ in rows if a.homework == 0)
    n = len(rows)
    pct = round(done / n * 100, 1) if n else None
    label, tone = roles.homework_band(
        pct if n >= roles.HOMEWORK_MIN_CHECKED else None)
    return {
        "checked": n, "done": done, "partial": partial, "missed": missed,
        "percent": pct,
        "label": label, "tone": tone,
        "enough": n >= roles.HOMEWORK_MIN_CHECKED,
    }

def _get_group_in_scope(db: Session, group_id: int, user: models.User) -> models.Group:
    """Fetch a group and 404/403 it the way every lesson/billing/payroll
    endpoint below needs: not found, or outside the caller's branch.

    Ustoz uchun bundan ham tor: faqat O'Z guruhi. Aks holda ustoz
    manzil qatoriga boshqa guruh raqamini yozib, hamkasbining guruhini
    va o'quvchilarini ochib ko'rardi."""
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    if not _in_user_branches(db, user, group.branch_id):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")
    if user.role in tuple(roles.OWN_GROUPS_ONLY) and not _teacher_owns(
            db, group, user):
        if not _teacher_of_user(db, user):
            raise HTTPException(
                403, "Hisobingiz ustoz kartasiga bog'lanmagan. HR yoki "
                     "asoschi Xodimlar bo'limidan hisobni ustozga "
                     "biriktirishi kerak.")
        raise HTTPException(403, "Bu guruh sizga biriktirilmagan")
    return group

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

def _group_capacity(g: models.Group, rooms: dict) -> int | None:
    """Guruh sig'imi: avval o'zining chekloviga, keyin xona sig'imiga
    qaraydi. Ikkalasi ham yo'q bo'lsa - hisoblab bo'lmaydi."""
    if g.capacity:
        return g.capacity
    r = rooms.get(g.room_id)
    return r.capacity if r else None

def _notify_discount_approvers(db: Session, d, st, extra: str = "") -> None:
    """Chegirma so'rovi jimgina yotib qolmasin.

    2026-08-12, Jahongir: "Chegirma sorovi jonatsa administrator
    kimlarga vazifa bolib tushadi tasdiqlash, filial rahbari,
    moliyachiga tushsin". Shuning uchun so'rov TASDIQLOVCHILARNING
    HAR BIRIGA alohida vazifa bo'lib tushadi: o'quvchi filialining
    rahbari, moliya direktori va asoschi.
    """
    label = roles.DISCOUNT_TYPE_LABELS.get(d.kind, d.kind)
    size = (f"{d.percent:.0f}%" if d.percent
            else (f"{d.amount:,.0f} so'm" if d.amount else "—"))
    title = f"Chegirma so'rovi #{d.id} — {st.full_name}"
    body = (f"{label} · {size}\n"
            f"O'quvchi: {st.full_name}\n"
            f"Sabab: {d.reason or '—'}\n"
            f"So'ragan: {d.requested_by or '—'}\n"
            + (extra + "\n" if extra else "")
            + "Tasdiqlash: shu vazifaning ichidagi tugmadan yoki "
              "bosh sahifadagi \"Chegirma so'rovlari\" blokidan.")
    seen = set()
    for r in roles.DISCOUNT_APPROVE:
        q = db.query(models.User).filter(models.User.role == r,
                                         models.User.is_active == 1)
        # Filial rahbari - FAQAT o'sha filialniki. Moliyachi va
        # asoschi butun tashkilot bo'yicha ko'radi.
        if r == roles.BRANCH_MANAGER and st.branch_id:
            q = q.filter(models.User.branch_id == st.branch_id)
        for u in q.all():
            if u.id in seen:
                continue
            seen.add(u.id)
            if db.query(models.Task).filter(
                    models.Task.title == title,
                    models.Task.assignee_id == u.id).first():
                continue
            t = models.Task(
                title=title, description=body, assignee_id=u.id,
                branch_id=st.branch_id,
                deadline=date.today() + timedelta(days=2),
                priority="high", source="manual", created_by="Tizim")
            db.add(t)
            db.flush()
            _ensure_public_id(db, "task", t)
    db.commit()


def _norm_surname(full_name: str) -> str:
    """Familiyani solishtirish uchun soddalashtiradi.

    2026-08-12, Jahongir: "agar bir xil familya bo'lsa, qiz bolada
    oxir fozilova o'gil bolada fozilov bo'lsa ham avtomat tizim
    tasdiqlayversin". O'zbekchada ayol familiyasi -ova/-eva bilan
    tugaydi, shuning uchun -a tashlanadi. Apostrof va o'/g' turli
    belgilar bilan yozilishi mumkin - ular ham tenglashtiriladi.
    """
    if not full_name:
        return ""
    w = full_name.strip().split()
    if not w:
        return ""
    x = w[0].lower()
    for ch in ("\u02bb", "\u02bc", "\u2018", "\u2019", "`", "'", "\u00b4"):
        x = x.replace(ch, "")
    x = x.replace("\u0451", "\u0435")
    # ...ova -> ...ov, ...eva -> ...ev, ...yeva -> ...yev
    for suf in ("ova", "eva", "yeva", "ova\u02bb"):
        if x.endswith(suf):
            x = x[:-1]
            break
    else:
        # Ruscha yozuvda ham shunday: -\u043e\u0432\u0430 / -\u0435\u0432\u0430
        for suf in ("\u043e\u0432\u0430", "\u0435\u0432\u0430"):
            if x.endswith(suf):
                x = x[:-1]
                break
    return x


def _same_surname(a: str, b: str) -> bool:
    """Ikki F.I.SH bir familiyadanmi (Fozilov = Fozilova)."""
    na, nb = _norm_surname(a), _norm_surname(b)
    return bool(na) and na == nb


def _do_family_link(db: Session, a: models.Student, b: models.Student,
                    username: str = "Tizim") -> dict:
    """Ikki o'quvchini BITTA ota-onaga (Parent) bog'laydi.

    Bog'lanish bitta yozuv orqali bo'lgani uchun ikki tomonlama -
    ikkinchisini qayta bog'lash shart emas (Jahongir, 2026-08-12).
    Oilaviy chegirmani tizim shu bog'lanishdan o'zi hisoblaydi.
    """
    moved = None
    if a.parent_id and b.parent_id and a.parent_id != b.parent_id:
        old_pid = b.parent_id
        for x in db.query(models.Student).filter(
                models.Student.parent_id == old_pid).all():
            x.parent_id = a.parent_id
        moved = old_pid
    elif a.parent_id:
        b.parent_id = a.parent_id
    elif b.parent_id:
        a.parent_id = b.parent_id
    else:
        fam = (a.full_name or "").strip().split(" ")[0] or "Oila"
        p = models.Parent(full_name=f"{fam} oilasi",
                          phone=a.parent_phone or b.parent_phone or None,
                          branch_id=a.branch_id or b.branch_id,
                          created_by=username)
        db.add(p); db.commit(); db.refresh(p)
        _ensure_public_id(db, "parent", p)
        a.parent_id = p.id
        b.parent_id = p.id
    db.commit()

    kids = (db.query(models.Student)
            .filter(models.Student.parent_id == a.parent_id).all())
    pct = _family_discount_percent(db, a)
    active = sum(1 for k in kids if k.status == "active")
    return {
        "parent_id": a.parent_id,
        "merged_parent_id": moved,
        "family_percent": pct,
        "min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "children": [{"id": k.id, "full_name": k.full_name,
                      "status": k.status} for k in kids],
        "active_children": active,
        "message": (
            f"Bog'landi \u2014 oilada {active} ta faol farzand, har biriga "
            f"{pct:.0f}% oilaviy chegirma avtomat hisoblanadi."
            if pct else
            f"Bog'landi. Oilaviy chegirma uchun kamida "
            f"{roles.FAMILY_DISCOUNT_MIN_CHILDREN} ta FAOL farzand kerak."),
    }


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
    # Asoschi 100% gacha qo'ya olgani uchun hisobda ham mutlaq
    # chegara 100% (oddiy chegirmalar yaratishda baribir 50% da
    # to'xtatiladi - finance.create_discount).
    return min(roles.DISCOUNT_ABSOLUTE_CAP, round(total, 2))

def _visible_discounts(db: Session, student_id: int) -> list:
    """O'quvchi/ota-ona portalida ko'rinadigan chegirmalar.

    2026-08-12, Jahongir: "o'quvchiga chegirmani nega olgani va qancha
    chegirmasi qachongacha borligi ko'rinib tursin, lekin individual
    ruxsat berilganlarga ko'rinmasin" - hidden=1 bo'lganlar
    KO'RSATILMAYDI."""
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == student_id,
                    models.Discount.status == "active").all())
    out = []
    for d in rows:
        if getattr(d, "hidden", 0):
            continue
        if not _discount_alive(d):
            continue
        out.append({
            "percent": d.percent,
            "amount": d.amount,
            "kind_label": roles.DISCOUNT_TYPE_LABELS.get(d.kind, d.kind),
            "reason": d.reason,
            "until": d.end_date.isoformat() if d.end_date else None,
        })
    return out


def _discount_out(db: Session, d: models.Discount) -> dict:
    ref = db.query(models.Student).get(d.referrer_student_id) if d.referrer_student_id else None
    emp = db.query(models.User).get(d.staff_user_id) if d.staff_user_id else None
    return {
        "id": d.id,
        "hidden": bool(getattr(d, "hidden", 0)),
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

def _trial_attendance(db: Session, student_id: int) -> list:
    """Sinovda bo'lgan o'quvchining KELGAN darslari, sana bo'yicha."""
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == student_id,
                    # 1 = keldi, 2 = kech keldi — ikkalasi ham kelgan
                    models.Attendance.present.in_((1, 2)))
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
    if _charge_skipped(db, s.id, period):
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

    # Xuddi shu sabab bilan (yuqoridagi izohga qarang) main orqali
    # dinamik chaqiramiz - entry.py buni almashtirishi mumkin.
    import main as _main
    charge = _main._charge_from_activation(db, s, on, user)

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

def _branch_scope_ids(db: Session, user, branch_id: int | None) -> list | None:
    """Foydalanuvchi ko'ra oladigan filiallar. None - hammasi."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        return [user.branch_id]
    if branch_id:
        return [branch_id]
    return None

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
        # Ustozga tajriba OYDA emas YILDA ko'rsatiladi: "42 oy" degani
        # odamga hech narsa anglatmaydi, "3.5 yil" anglatadi
        "years": roles.tenure_years(months),
        "tenure_text": roles.tenure_years_text(months),
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
        # Oy o'rtasida ko'tarilgan bo'lsa - keyingi oydan kuchga kiradi
        "pending_grade": t.pending_grade,
        "pending_label": roles.GRADE_LABELS.get(t.pending_grade or ""),
        "pending_from": (t.pending_grade_from.isoformat()
                         if t.pending_grade_from else None),
        "pending_rate": (gm[t.pending_grade].rate_per_student
                         if t.pending_grade in gm else None),
        "skill_score_from": "oxirgi dars baholash",
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
    o'tgan oyning darslari eski stavkada qolaveradi.

    `on` kelajakdagi sana bo'lsa (masalan keyingi oyning 1-sanasi),
    daraja hozir o'zgarmaydi — kutish holatiga yoziladi va o'sha kuni
    o'zi almashadi."""
    on = on or date.today()
    today = date.today()
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

    if on > today:
        # Keyingi oydan kuchga kiradi: bu oy eski stavkada yopiladi
        t.pending_grade = to_key
        t.pending_grade_from = on
        return ev

    t.grade = to_key
    t.grade_since = on
    t.pending_grade = None
    t.pending_grade_from = None
    if after:
        _sync_group_rates(db, t, after.rate_per_student or 0)
    return ev

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
    # Avval aniq bog'lanish (akkaunt ochilganda yoziladi), keyingina
    # ism bo'yicha — eski yozuvlar uchun.
    t = (db.query(models.Teacher)
         .filter(models.Teacher.user_id == user.id).first())
    if t:
        return t
    t = (db.query(models.Teacher)
         .filter(models.Teacher.full_name == user.full_name).first())
    if t:
        if not t.user_id:
            t.user_id = user.id
            db.commit()
        return t
    # Support teacher uchun karta avtomat ochiladi — "ulanmagan"
    # degan yozuv bilan kabinet bo'sh turmasin.
    if user.role == roles.SUPPORT_TEACHER:
        t = models.Teacher(full_name=user.full_name,
                           branch_id=user.branch_id, is_active=1,
                           user_id=user.id)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t
    return None

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
        mine = mine.filter(_branch_in(db, user, models.Lead.branch_id))
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

def _plan_fakt_revenue_plan(db: Session, branch_id, year: int,
                            month: int) -> float:
    """Reja-Faktdagi TUSHUM rejasi shu kalendar oy uchun.

    2026-08-12, Jahongir: "sotuv rejasi ko'rinmayapti, lekin men
    kiritib qo'yganman Bekobod 1 nikini keyingi o'quv yili uchun" -
    u rejani Reja-Fakt bo'limiga kiritgan (SMM jadvaliga emas).
    Marketolog kartasi endi o'sha yerdan ham o'qiydi: tushum rejasi =
    o'rtacha chek x (yangi + eski to'lovlar soni rejasi) - Reja-Fakt
    dagi avtomat hisob bilan bir xil."""
    if not branch_id:
        return 0.0
    sy = year if month >= 9 else year - 1     # o'quv yili boshi
    rows = (db.query(models.PlanTarget)
            .filter(models.PlanTarget.year == sy,
                    models.PlanTarget.branch_id == branch_id,
                    models.PlanTarget.month == month,
                    models.PlanTarget.metric.in_(
                        ("new_payments", "old_payments", "revenue")))
            .all())
    vals = {r.metric: r.value for r in rows}
    if vals.get("revenue"):
        return float(vals["revenue"])         # eski qo'lda kiritilganlar
    cnt = (vals.get("new_payments") or 0) + (vals.get("old_payments") or 0)
    if not cnt:
        return 0.0
    from finance import _avg_check_recent
    ac = _avg_check_recent(db, branch_id) or 0
    return float(round(ac * cnt, 0))


def _smm_sales_state(db: Session, branch_id, year: int, month: int) -> dict:
    """Marketolog sotuv rejasi holati: reja, fakt (shu oy tushumi,
    filial bo'yicha), foiz, bonus, yangi to'lovlar soni va hozirgi
    o'quvchilar soni (Jahongir jadvali, 2026-08-11)."""
    m_start, m_end = billing.month_bounds(year, month)
    d0, d1 = _utc_window(m_start, m_end)

    plan_row = (db.query(models.SmmSalesPlan)
                .filter(models.SmmSalesPlan.branch_id == branch_id,
                        models.SmmSalesPlan.year == year,
                        models.SmmSalesPlan.month == month).first()
                if branch_id else None)
    plan = float(plan_row.amount) if plan_row else 0.0
    if not plan:
        plan = _plan_fakt_revenue_plan(db, branch_id, year, month)

    pq = (db.query(models.Payment, models.Student)
          .join(models.Student,
                models.Payment.student_id == models.Student.id)
          .filter(models.Payment.kind == "payment",
                  models.Payment.created_at >= d0,
                  models.Payment.created_at <= d1))
    if branch_id:
        pq = pq.filter(models.Student.branch_id == branch_id)
    # Har o'quvchining ENG BIRINCHI to'lovi shu oyga tushsa - yangi
    # mijoz (dashboard'dagi hisob bilan bir xil mantiq)
    first_dates = dict(
        db.query(models.Payment.student_id,
                 func.min(models.Payment.created_at))
        .filter(models.Payment.kind == "payment")
        .group_by(models.Payment.student_id).all())
    fact = 0.0
    new_count = 0
    for p, st in pq.all():
        fact += p.amount or 0
        if first_dates.get(st.id) == p.created_at:
            new_count += 1

    sq = db.query(models.Student).filter(
        models.Student.status == "active")
    if branch_id:
        sq = sq.filter(models.Student.branch_id == branch_id)
    students_now = sq.count()

    percent = round(fact / plan * 100, 1) if plan else None
    bonus, label = (roles.smm_sales_bonus(percent)
                    if percent is not None else (0, "Reja kiritilmagan"))
    return {
        "plan": round(plan, 0), "fact": round(fact, 0),
        "percent": percent, "bonus": bonus, "bonus_label": label,
        "new_payments_count": new_count, "students_now": students_now,
    }


def _my_marketing_cards(db: Session, user: models.User) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())
    leads = db.query(models.Lead).filter(models.Lead.created_at >= d0).all()
    conv = [l for l in leads if l.stage == "converted"]
    spend = sum(e.amount for e in db.query(models.Expense).filter(
        models.Expense.category == "ads",
        models.Expense.date >= m_start).all())
    cards = [
        _card("Shu oy lidlar", len(leads), None, "brand", "/marketing"),
        _card("O'quvchiga aylandi", len(conv), None, "good", "/marketing"),
        _card("Reklama xarajati", round(spend, 2), None, "plain", "/marketing"),
        _card("Bitta lid narxi",
              round(spend / len(leads)) if leads else 0,
              "CAC", "plain", "/analytics"),
    ]
    # SOTUV REJASI VA BONUS (Jahongir, 2026-08-11): reja/fakt, foiz,
    # bonus jadval bo'yicha + yangi to'lovlar soni va o'quvchilar soni
    try:
        st8 = _smm_sales_state(db, user.branch_id, today.year, today.month)
        if st8["percent"] is None:
            # Joriy oyda reja yo'q - keyingi oydan boshlanayotgan
            # bo'lsa (masalan, sentabrdan) shuni ko'rsatamiz
            ny, nm = ((today.year + 1, 1) if today.month == 12
                      else (today.year, today.month + 1))
            nxt = _smm_sales_state(db, user.branch_id, ny, nm)
            if nxt["plan"]:
                cards.append(_card(
                    f"Sotuv rejasi ({roles.UZ_MONTHS[nm - 1].lower()})",
                    f"{nxt['plan']:,.0f} so'm".replace(",", " "),
                    f"{roles.UZ_MONTHS[nm - 1]}dan kuchga kiradi",
                    "brand", "/marketing"))
            else:
                cards.append(_card(
                    "Sotuv rejasi (oy)", "Reja kiritilmagan",
                    "Marketing bo'limida asoschi kiritadi", "amber",
                    "/marketing"))
        else:
            pct = st8["percent"]
            tone = ("good" if pct >= 100
                    else "amber" if pct >= 80 else "bad")
            cards.append(_card(
                "Sotuv rejasi bajarilishi", f"{pct}%",
                f"reja {st8['plan']:,.0f} · fakt {st8['fact']:,.0f}"
                .replace(",", " "), tone, "/marketing"))
            cards.append(_card(
                "Sotuv bonusi", st8["bonus"],
                st8["bonus_label"], tone, "/marketing"))
        cards.append(_card(
            "Yangi to'lovlar soni", st8["new_payments_count"],
            "shu oy, birinchi marta to'laganlar", "brand", "/marketing"))
        cards.append(_card(
            "Hozirgi o'quvchilar", st8["students_now"],
            "faol o'quvchilar soni", "plain", "/students"))
    except Exception:
        pass
    return cards

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

GRID_START_MIN = 6 * 60      # 06:00

GRID_END_MIN = 22 * 60       # 22:00

def _student_payments(db: Session) -> dict:
    rows = (db.query(models.Payment.student_id,
                     func.sum(models.Payment.amount),
                     func.count(models.Payment.id))
            .filter(models.Payment.kind == "payment")
            .group_by(models.Payment.student_id).all())
    return {sid: {"total": amt or 0.0, "count": cnt or 0}
            for sid, amt, cnt in rows}

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
                "date_label": roles.uz_date_full(nxt),
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


def _level_for_points(points: int) -> dict:
    """Ball -> daraja + keyingi darajagacha qolgan yo'l.

    Bitta joyda: umumiy daraja ham, har bir ko'nikma darajasi ham
    AYNAN shu zinadan yuradi (roles.ENG_LEVELS,
    roles.PRACTICE_POINTS_PER_LEVEL) — ikki xil hisob-kitob bo'lib
    ketmasligi uchun."""
    per = roles.PRACTICE_POINTS_PER_LEVEL
    idx = min(len(roles.ENG_LEVELS) - 1, int(points) // per)
    cur = roles.ENG_LEVELS[idx]
    is_last = idx >= len(roles.ENG_LEVELS) - 1
    in_level = int(points) - idx * per
    nxt = None if is_last else roles.ENG_LEVELS[idx + 1]
    return {
        "points": int(points),
        "level": cur,
        "max_level": is_last,
        "next": None if is_last else {
            "label": nxt["label"], "ielts": nxt["ielts"], "cefr": nxt["cefr"],
            "points_left": per - in_level,
            "progress_percent": round(in_level * 100 / per, 1),
        },
    }


def _skill_points(db: Session, student_id: int) -> dict:
    """Har bir ko'nikma bo'yicha yig'ilgan ball (to'g'ri javoblar).

    Ikkita manbadan qo'shiladi:
      1. ExerciseResult — ustoz kiritgan mashq natijalari (skill
         ustuni bilan; eski, skill'siz yozuvlar ko'nikmaga sanalmaydi
         lekin umumiyga sanaladi);
      2. VocabAttempt — o'quvchining Jony Student ilovasidagi lug'at
         o'yinlari (har to'g'ri javob 1 ball, "vocabulary" ko'nikmasi).
    """
    out = {k: 0 for k in roles.SKILL_KEYS}
    rows = (db.query(models.ExerciseResult.skill,
                     func.coalesce(func.sum(models.ExerciseResult.correct), 0))
            .filter(models.ExerciseResult.student_id == student_id)
            .group_by(models.ExerciseResult.skill).all())
    for skill, correct in rows:
        if skill in out:
            out[skill] += int(correct or 0)
    vocab = (db.query(func.count(models.VocabAttempt.id))
             .filter(models.VocabAttempt.student_id == student_id,
                     models.VocabAttempt.correct == 1).scalar() or 0)
    out["vocabulary"] += int(vocab)
    # Grammar mashqlari (2026-08-10): har TO'G'RI yechilgan savol
    # 1 ball, lekin bitta savol faqat BIR marta sanaladi (distinct) -
    # bitta oson savolni qayta-qayta yechib ball yig'ib bo'lmaydi.
    gram = (db.query(func.count(
                func.distinct(models.GrammarAttempt.question_id)))
            .filter(models.GrammarAttempt.student_id == student_id,
                    models.GrammarAttempt.correct == 1).scalar() or 0)
    out["grammar"] += int(gram)
    # Listening/Reading/Writing/Speaking mashqlari (2026-08-10):
    # har ko'nikmada distinct to'g'ri yechilgan mashq = 1 ball.
    rows2 = (db.query(models.SkillAttempt.skill,
                      func.count(func.distinct(models.SkillAttempt.ref)))
             .filter(models.SkillAttempt.student_id == student_id,
                     models.SkillAttempt.correct == 1)
             .group_by(models.SkillAttempt.skill).all())
    for skill, cnt in rows2:
        if skill in out:
            out[skill] += int(cnt or 0)
    return out


def _skills_card(db: Session, student_id: int) -> dict:
    """Jony Student uchun: UMUMIY daraja + har bir ko'nikma darajasi.

    Umumiy ball = barcha mashq natijalari (skill'siz eskilari ham) +
    lug'at o'yinlari — ya'ni hech bir ball yo'qolmaydi. Ko'nikma
    kesimi esa faqat belgilangan yozuvlardan chiqadi."""
    total_ex = (db.query(
        func.coalesce(func.sum(models.ExerciseResult.correct), 0))
        .filter(models.ExerciseResult.student_id == student_id)
        .scalar() or 0)
    vocab = (db.query(func.count(models.VocabAttempt.id))
             .filter(models.VocabAttempt.student_id == student_id,
                     models.VocabAttempt.correct == 1).scalar() or 0)
    gram = (db.query(func.count(
                func.distinct(models.GrammarAttempt.question_id)))
            .filter(models.GrammarAttempt.student_id == student_id,
                    models.GrammarAttempt.correct == 1).scalar() or 0)
    prac = (db.query(func.count(func.distinct(
                models.SkillAttempt.skill + ":" + models.SkillAttempt.ref)))
            .filter(models.SkillAttempt.student_id == student_id,
                    models.SkillAttempt.correct == 1).scalar() or 0)
    per_skill = _skill_points(db, student_id)
    overall = _level_for_points(
        int(total_ex) + int(vocab) + int(gram) + int(prac))
    return {
        "overall": overall,
        "skills": [{
            "key": k,
            "label": roles.SKILL_LABELS[k],
            "tone": roles.SKILL_TONE[k],
            **_level_for_points(per_skill[k]),
        } for k in roles.SKILL_KEYS],
        "points_per_level": roles.PRACTICE_POINTS_PER_LEVEL,
        "levels": roles.ENG_LEVELS,
    }

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
                        >= _utc_window(start, end)[0],
                        models.XpTransaction.created_at
                        <= _utc_window(start, end)[1])
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

def _league_out(lg, count: int = 0) -> dict:
    return {
        "id": lg.id, "key": lg.key, "name": lg.name, "rank": lg.rank,
        "minimum_xp": lg.minimum_xp, "maximum_xp": lg.maximum_xp,
        "color": lg.color, "icon": lg.icon,
        "description": lg.description,
        "reward_coin": lg.reward_coin or 0,
        "is_active": bool(lg.is_active), "students": count,
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
        # Uy vazifasi bolaning o'ziga ham ko'rinsin — XP shundan
        # keladi, demak u nimadan kelayotganini bilishi kerak
        "homework": _homework_stats(db, s.id,
                                    since=today - timedelta(days=90)),
    })
    return card

def _criteria(db: Session, key: str) -> list:
    return (db.query(models.RubricCriterion)
            .filter(models.RubricCriterion.rubric_key == key,
                    models.RubricCriterion.is_active == 1)
            .order_by(models.RubricCriterion.order_no,
                      models.RubricCriterion.id).all())

def _observation_out(db: Session, o: models.LessonObservation,
                     full: bool = False) -> dict:
    _k, label, tone = roles.rubric_band(o.percent or 0)
    row = {
        "id": o.id, "rubric_key": o.rubric_key,
        "rubric": roles.RUBRIC_LABELS.get(o.rubric_key, o.rubric_key),
        "target_type": o.target_type,
        "stage": o.stage,
        "stage_label": roles.STAGE_LABELS.get(o.stage or "", "Baholash"),
        "stage_tone": roles.STAGE_TONE.get(o.stage or "", "slate"),
        "attempt": o.attempt or 1,
        "teacher_id": o.teacher_id, "candidate_id": o.candidate_id,
        "teacher": o.teacher.full_name if o.teacher else None,
        "date": o.date.isoformat() if o.date else None,
        "total": o.total or 0, "max_total": o.max_total or 0,
        "percent": o.percent or 0,
        "band": o.band, "band_label": label, "tone": tone,
        "observer": o.observer,
        "strengths": o.strengths, "weaknesses": o.weaknesses,
        "note": o.note,
    }
    if full:
        crit = {c.id: c for c in db.query(models.RubricCriterion).all()}
        row["scores"] = sorted([{
            "criterion_id": s.criterion_id,
            "no": crit[s.criterion_id].order_no if s.criterion_id in crit else 0,
            "text": crit[s.criterion_id].text if s.criterion_id in crit else "—",
            "points": crit[s.criterion_id].points if s.criterion_id in crit else 0,
            "fact": s.fact or 0,
            "note": s.note,
        } for s in o.scores], key=lambda r: r["no"])
    return row

def _seed_brand(db: Session) -> None:
    """Brandbookdagi qoidalarni bazaga yozadi. Mavjudini o'zgartirmaydi."""
    def add(section, key, title, value=None, note=None, kind=None,
            source="PDF", pos=0):
        row = db.query(models.BrandRule).filter(
            models.BrandRule.section == section,
            models.BrandRule.key == key).first()
        if row:
            return
        db.add(models.BrandRule(
            section=section, key=key, title=title, value=value, note=note,
            kind=kind, source=source, position=pos))

    for i, (k, name, hexv, kind, note) in enumerate(roles.BRAND_COLORS):
        add("color", k, name, hexv, note, kind,
            "TO'LDIRILDI" if note.startswith("TO'LDIRILDI") else "PDF", i)
    for i, (name, label, note) in enumerate(roles.BRAND_FONTS):
        add("font", name, name, label, note, None,
            "TO'LDIRILDI" if note.startswith("TO'LDIRILDI") else "PDF", i)
    for i, (title, src, note) in enumerate(roles.LOGO_RULES):
        add("logo", f"logo{i}", title, None, note, "do", src, i)
    for i, txt in enumerate(roles.LOGO_DONTS):
        add("dont", f"dont{i}", txt, None, None, "dont", "TO'LDIRILDI", i)
    for i, (title, kind, note) in enumerate(roles.TONE_RULES):
        add("tone", f"tone{i}", title, None, note, kind, "TO'LDIRILDI", i)
    for i, (name, size, note) in enumerate(roles.SOCIAL_SPECS):
        add("spec", f"spec{i}", name, size, note, None, "TO'LDIRILDI", i)
    for i, (label, value, note) in enumerate(roles.BRAND_CONTACTS):
        add("contact", f"c{i}", label, value, note or None, None,
            "TO'LDIRILDI" if note else "PDF", i)
    add("word", "word", roles.BRAND_WORD, roles.BRAND_WORD,
        roles.BRAND_WORD_NOTE, None, "TO'LDIRILDI", 0)
    db.commit()

def _seed_kb(db: Session) -> None:
    """Boshlang'ich maqolalar — brandbookdan kelib chiqqan holda."""
    seed = [
        ("Post chiqarishdan oldingi tekshiruv", "process",
         "Har bir post joylashdan oldin shu ro'yxat bo'yicha "
         "tekshiriladi:\n\n"
         "1. Matndagi har bir raqam va natija haqiqiymi? "
         "O'ylab topilgan raqam bir marta ishlaydi, keyin ishonchni "
         "butunlay yo'q qiladi.\n"
         "2. Rasmdagi bolalarning roziligi bormi? Media "
         "kutubxonada holati \"Ijtimoiy tarmoqqa mumkin\" bo'lsin.\n"
         "3. Logotip to'g'ri variantdami, atrofida bo'sh joy bormi?\n"
         "4. Faqat brend ranglari ishlatilganmi?\n"
         "5. Birinchi jumla ushlab qoladimi? Ovoz chiqarib o'qing.\n"
         "6. Aloqa ma'lumotlari to'g'rimi?\n"
         "7. Narx yozilgan bo'lsa, hozirgi narxmi?"),
        ("Brend so'zi: Muhit", "brand",
         "Jony nomi eshitilganda odam ongida bitta so'z tiklanishi "
         "kerak — \"muhit\".\n\n"
         "Ya'ni gap faqat dastur, ustoz yoki narx haqida emas. Gap "
         "bolani o'rab turgan butun muhit haqida: kim bilan o'tiradi, "
         "qanday kayfiyatda keladi, xato qilganda nima bo'ladi.\n\n"
         "Amalda: har postda \"muhit\" so'zini majburan tiqishtirish "
         "shart emas — lekin postning MAZMUNI shu tushunchani aks "
         "ettirsin. Yutuq haqida yozganda ham natijani muhitga bog'lang: "
         "\"bunday natija tasodifan kelmaydi\"."),
        ("Rozilik qanday olinadi", "crisis",
         "Bolaning rasmi yoki videosi ijtimoiy tarmoqqa chiqishidan "
         "oldin ota-onadan yozma rozilik olinadi.\n\n"
         "Rozilik muddatli bo'ladi — odatda o'quv yili oxirigacha. "
         "Muddat tugasa material avtomat \"taqiqlangan\"ga o'tadi.\n\n"
         "Ota-ona keyin fikrini o'zgartirsa: material darhol "
         "\"taqiqlangan\" qilinadi VA allaqachon joylangan postlar "
         "o'chiriladi. Bahslashilmaydi."),
        ("Salbiy izohga qanday javob beriladi", "crisis",
         "1. Darhol javob berilmaydi — 15 daqiqa kutiladi, his-tuyg'u "
         "bilan yozilgan javob vaziyatni yomonlashtiradi.\n"
         "2. Ochiq javob qisqa va odamiy bo'ladi: eshitdik, "
         "tushundik, shaxsan bog'lanamiz.\n"
         "3. Batafsil muhokama DM'ga o'tkaziladi.\n"
         "4. Izoh o'chirilmaydi — haqorat yoki spam bo'lmasa.\n"
         "5. Agar shikoyat asosli bo'lsa, tizimda \"Shikoyat\" deb "
         "belgilanadi va tegishli bo'limga yuboriladi.\n\n"
         "Bitta yaxshi javob berilgan salbiy izoh — o'nta maqtovdan "
         "kuchliroq ishonch beradi."),
        ("Sifatli engagement nima", "process",
         "Like eng arzon ko'rsatkich — barmoq bilan bosiladi, hech "
         "narsa anglatmaydi.\n\n"
         "Tizimda engagement shunday hisoblanadi:\n"
         "like ×1 · izoh ×2 · saqlash ×3 · ulashish ×4 · DM ×5\n\n"
         "Chunki DM yozgan odam sotuvga eng yaqin, saqlagan odam "
         "keyin qaytadi. Shuning uchun hisobotda \"qancha like\" emas, "
         "\"qancha DM va sotuv\" ko'riladi."),
        ("Reels uchun texnik talablar", "tool",
         "O'lcham: 1080×1920 (9:16).\n"
         "Xavfsiz zona: pastdan 250 px, yuqoridan 150 px — bu joyni "
         "Instagram interfeysi bosib qoladi, muhim matn qo'yilmaydi.\n"
         "Birinchi 3 soniya — hal qiluvchi. Logotip bilan boshlanmaydi, "
         "hikoya bilan boshlanadi.\n"
         "Subtitr majburiy — ko'pchilik ovozsiz ko'radi."),
    ]
    for title, cat, body in seed:
        if db.query(models.KbArticle).filter(
                models.KbArticle.title == title).first():
            continue
        db.add(models.KbArticle(title=title, category=cat, body=body,
                                reviewed_at=date.today()))
    db.commit()

def _link_teacher_accounts(db: Session) -> None:
    """Ism bo'yicha bog'langan eski akkauntlarni ID'ga o'tkazadi.
    Bir marta ishlaydi — keyin user_id to'lgan bo'ladi."""
    loose = db.query(models.Teacher).filter(
        models.Teacher.user_id.is_(None)).all()
    if not loose:
        return
    taken = {tid for (tid,) in db.query(models.Teacher.user_id)
             .filter(models.Teacher.user_id.isnot(None)).all()}
    by_name: dict = {}
    for u in (db.query(models.User)
              .filter(models.User.role == roles.TEACHER).all()):
        by_name.setdefault(u.full_name, []).append(u)
    changed = False
    for t in loose:
        # Bir xil ismli bir nechta akkaunt bo'lsa — band bo'lmaganini
        # olamiz, ya'ni bitta login ikki ustozga tegmaydi.
        free = [u for u in by_name.get(t.full_name, [])
                if u.id not in taken]
        if free:
            t.user_id = free[0].id
            taken.add(free[0].id)
            changed = True
    if changed:
        db.commit()

def _hr_task(db: Session, *, title: str, body: str,
             to_roles: list, branch_id=None, days: int = 2,
             priority: str = "normal") -> None:
    """HR jarayonidagi qarorlar jimgina o'tib ketmasin — tizimda
    vazifa bo'lib ko'rinadi. Bir xil sarlavhali vazifa ikki marta
    yaratilmaydi."""
    if db.query(models.Task).filter(models.Task.title == title).first():
        return
    q = db.query(models.User).filter(models.User.role.in_(to_roles),
                                     models.User.is_active == 1)
    who = None
    if branch_id:
        who = q.filter(models.User.branch_id == branch_id).first()
    who = who or q.first()
    task = models.Task(
        title=title, description=body,
        assignee_id=who.id if who else None,
        branch_id=branch_id,
        deadline=date.today() + timedelta(days=days),
        priority=priority, source="manual", created_by="Tizim")
    db.add(task)
    db.flush()
    _ensure_public_id(db, "task", task)

def _hr_task_for(db: Session, user_id: int, *, title: str, body: str,
                 branch_id=None, days: int = 2) -> None:
    """Aniq bir xodimga vazifa."""
    if db.query(models.Task).filter(models.Task.title == title).first():
        return
    task = models.Task(
        title=title, description=body, assignee_id=user_id,
        branch_id=branch_id,
        deadline=date.today() + timedelta(days=days),
        priority="normal", source="manual", created_by="Tizim")
    db.add(task)
    db.flush()
    _ensure_public_id(db, "task", task)

def _seed_hr_structure(db: Session) -> None:
    for i, (key, name, desc) in enumerate(roles.DEPARTMENTS):
        if not db.query(models.Department).filter(
                models.Department.key == key).first():
            db.add(models.Department(key=key, name=name, description=desc,
                                     position=i))
    db.commit()

    deps = {d.key: d.id for d in db.query(models.Department).all()}
    for key, name, dep, role, months, trial in roles.POSITIONS:
        if db.query(models.Position).filter(
                models.Position.key == key).first():
            continue
        db.add(models.Position(
            key=key, name=name, department_id=deps.get(dep),
            system_role=role, probation_months=months,
            trial_required=1 if trial else 0))
    db.commit()

def _support_assigned_groups(db: Session, user) -> list:
    """Support teacherga biriktirilgan guruhlar (SupportAssignment,
    user_id bo'yicha). Jadvali va o'quvchilari shu yerdan chiqadi."""
    gids = [a.group_id for a in db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.user_id == user.id,
                    models.SupportAssignment.group_id.isnot(None)).all()]
    if not gids:
        return []
    return (db.query(models.Group).filter(models.Group.id.in_(gids))
            .order_by(models.Group.name).all())

def _cabinet_groups(db: Session, user, t) -> list:
    """Kabinet guruhlari: ustozga o'z guruhlari, support teacherga —
    biriktirilganlari."""
    if user.role == roles.SUPPORT_TEACHER:
        return _support_assigned_groups(db, user)
    return _my_groups(db, t.id)

def _my_groups(db: Session, teacher_id: int) -> list:
    return (db.query(models.Group)
            .filter(models.Group.teacher_id == teacher_id)
            .order_by(models.Group.name).all())

def _reschedule_usage(db: Session, teacher_id: int,
                      for_date: date | None = None) -> dict:
    """Kvota KO'CHIRILAYOTGAN DARS oyi bo'yicha hisoblanadi.

    "Bir oyda 2 marta" degani — o'sha oyning 2 ta darsi. Agar hisob
    so'rov yuborilgan kun bo'yicha yuritilsa, ustoz oy oxirida kelasi
    oyning darslarini surib, chegarani aylanib o'tardi."""
    today = date.today()
    for_date = for_date or today
    month_start = for_date.replace(day=1)
    window_start = today - timedelta(days=roles.RESCHEDULE_WINDOW_DAYS)

    q = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.teacher_id == teacher_id,
        models.LessonReschedule.status.in_(roles.RESCHEDULE_DONE))
    # Kvota — USTOZNING o'z surishlari uchun. Rahbariyat bayram yoki
    # boshqa sabab bilan darsni ko'chirsa, ustoz buning uchun
    # javobgar emas va imkoni yeyilmasligi kerak.
    t = db.query(models.Teacher).get(teacher_id)
    if t and t.user_id:
        q = q.filter(or_(models.LessonReschedule.requested_by.is_(None),
                         models.LessonReschedule.requested_by == t.user_id))
    # Hisob SO'RALGAN dars sanasi bo'yicha — ustoz kelasi oyning
    # darsini bugun surib, oylik kvotani aylanib o'tolmasin
    used_month = q.filter(
        models.LessonReschedule.from_date >= month_start,
        models.LessonReschedule.from_date <= _month_end(for_date)).count()
    used_window = q.filter(
        models.LessonReschedule.from_date >= window_start).count()
    return roles.reschedule_quota(used_month, used_window)

def _month_end(d: date) -> date:
    if d.month == 12:
        return date(d.year, 12, 31)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)

def _resch_out(db: Session, r: models.LessonReschedule) -> dict:
    g = db.query(models.Group).get(r.group_id)
    t = db.query(models.Teacher).get(r.teacher_id) if r.teacher_id else None
    by = db.query(models.User).get(r.decided_by) if r.decided_by else None
    return {
        "id": r.id,
        "group_id": r.group_id, "group": g.name if g else None,
        "teacher": t.full_name if t else None,
        "from_date": r.from_date.isoformat(),
        "to_date": r.to_date.isoformat(),
        "from_time": r.from_time, "to_time": r.to_time,
        "shift_days": (r.to_date - r.from_date).days,
        "reason": r.reason,
        "reason_label": roles.RESCHEDULE_REASON_LABELS.get(r.reason or "",
                                                           "—"),
        "note": r.note,
        "status": r.status,
        "status_label": roles.RESCHEDULE_STATUS_LABELS.get(r.status, "—"),
        "status_tone": roles.RESCHEDULE_STATUS_TONE.get(r.status, "slate"),
        "auto_approved": bool(r.auto_approved),
        "decided_by": by.full_name if by else None,
        "decision_note": r.decision_note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

def _apply_reschedule(db: Session, r: models.LessonReschedule) -> None:
    """Jadvaldagi darsni yangi sanaga ko'chiradi. O'tilgan (held=1)
    darsga TEGILMAYDI — u tarix va ish haqi asosi."""
    ls = db.query(models.Lesson).filter(
        models.Lesson.group_id == r.group_id,
        models.Lesson.date == r.from_date).first()
    if ls and not ls.held:
        ls.date = r.to_date
        ls.note = ((ls.note or "") + " · ko'chirildi").strip()
        r.lesson_id = ls.id
    elif not ls:
        # Jadvalda hali yo'q bo'lsa yangi rejalashtirilgan dars ochamiz
        ls = models.Lesson(group_id=r.group_id, teacher_id=r.teacher_id,
                           date=r.to_date, held=0,
                           note="ko'chirilgan dars", created_by="Tizim")
        db.add(ls); db.flush()
        r.lesson_id = ls.id

def _book_out(db: Session, o: models.BookOrder) -> dict:
    t = db.query(models.Teacher).get(o.teacher_id) if o.teacher_id else None
    br = db.query(models.Branch).get(o.branch_id) if o.branch_id else None
    g = db.query(models.Group).get(o.group_id) if o.group_id else None
    by = db.query(models.User).get(o.decided_by) if o.decided_by else None
    items = db.query(models.BookOrderItem).filter(
        models.BookOrderItem.order_id == o.id).all()
    today = date.today()
    return {
        "id": o.id, "public_id": o.public_id,
        "teacher": t.full_name if t else None,
        "teacher_id": o.teacher_id,
        "branch": br.name if br else None, "branch_id": o.branch_id,
        "group": g.name if g else None, "group_id": o.group_id,
        "needed_by": o.needed_by.isoformat() if o.needed_by else None,
        "days_left": (o.needed_by - today).days if o.needed_by else None,
        "urgency": o.urgency or "normal",
        "urgency_label": roles.BOOK_URGENCY_LABELS.get(o.urgency or "normal"),
        "urgency_tone": roles.BOOK_URGENCY_TONE.get(o.urgency or "normal",
                                                    "slate"),
        "note": o.note,
        "status": o.status,
        "status_label": roles.BOOK_STATUS_LABELS.get(o.status, "—"),
        "status_tone": roles.BOOK_STATUS_TONE.get(o.status, "slate"),
        "is_open": o.status in roles.BOOK_OPEN_STATUSES,
        "decided_by": by.full_name if by else None,
        "decision_note": o.decision_note,
        "delivered_at": (o.delivered_at.isoformat()
                         if o.delivered_at else None),
        "task_id": o.task_id,
        "items": [{
            "id": i.id, "title": i.title, "level": i.level,
            "qty": i.qty, "delivered_qty": i.delivered_qty or 0,
            "note": i.note, "consumable_id": i.consumable_id,
        } for i in items],
        "total_qty": sum(i.qty for i in items),
        "titles": len(items),
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }

def _exam_order_out(db: Session, o: models.ExamOrder) -> dict:
    g = db.query(models.Group).get(o.group_id) if o.group_id else None
    t = db.query(models.Teacher).get(o.teacher_id) if o.teacher_id else None
    br = db.query(models.Branch).get(o.branch_id) if o.branch_id else None
    who = db.query(models.User).get(o.accepted_by) if o.accepted_by else None
    kind_label = roles.EXAM_KIND_LABELS.get(o.kind, o.kind)
    # Unit testda QAYSI unit ekani hamma joyda ko'rinsin (Jahongir:
    # "examinerlar ham bilib shu unitni testini chiqarib turadi")
    if o.kind == "unit" and o.unit_no:
        kind_label = f"{kind_label} — Unit {o.unit_no}"
    return {
        "id": o.id,
        "public_id": o.public_id,
        "group_id": o.group_id,
        "group": g.name if g else None,
        "level": g.level if g else None,
        "teacher_id": o.teacher_id,
        "teacher": t.full_name if t else None,
        "branch_id": o.branch_id,
        "branch": br.name if br else None,
        "date": o.date.isoformat() if o.date else None,
        "date_text": roles.uz_date_full(o.date),
        "time": o.time,
        "kind": o.kind,
        "kind_label": kind_label,
        "unit_no": o.unit_no,
        "students_count": o.students_count or 0,
        "note": o.note,
        "status": o.status,
        "status_label": roles.EXAM_ORDER_LABELS.get(o.status, o.status),
        "status_tone": roles.EXAM_ORDER_TONE.get(o.status, "slate"),
        "accepted_by": who.full_name if who else None,
        "accepted_at": o.accepted_at.isoformat() if o.accepted_at else None,
        "decision_note": o.decision_note,
        "reject_reason": o.reject_reason,
        "reject_reason_label": dict(
            roles.EXAM_ORDER_REJECT_REASONS).get(o.reject_reason),
        "exam_id": o.exam_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        # Ustoz ham, examiner ham AYNAN shu matnni ko'radi
        "message": roles.exam_order_message(
            teacher=t.full_name if t else "—",
            branch=br.name if br else "—",
            date_text=roles.uz_date_full(o.date),
            time_text=o.time or (g.lesson_time if g else None) or "—",
            kind=(kind_label or "").upper(),
            group=g.name if g else "—",
            students=o.students_count or 0,
            accepted_by=who.full_name if who else None,
            status=o.status,
            unit_no=o.unit_no if o.kind == "unit" else None),
    }

def _exam_order_form(db: Session, user: models.User) -> dict:
    return {
        "kinds": [{"key": k, "label": roles.EXAM_KIND_LABELS.get(k, k)}
                  for k in roles.EXAM_KINDS],
        "unit_count": roles.UNIT_COUNT,
        "min_notice_days": roles.EXAM_ORDER_MIN_NOTICE_DAYS,
        "max_ahead_days": roles.EXAM_ORDER_MAX_AHEAD_DAYS,
        "reject_reasons": [{"key": k, "label": l}
                           for k, l in roles.EXAM_ORDER_REJECT_REASONS],
        "statuses": [{"key": k, "label": l, "tone": t}
                     for k, l, t in roles.EXAM_ORDER_STATUSES],
    }

def _support_session_out(db: Session, r: models.SupportSession) -> dict:
    g = db.query(models.Group).get(r.group_id) if r.group_id else None
    return {
        "id": r.id, "teacher_id": r.teacher_id,
        "group_id": r.group_id, "group": g.name if g else None,
        "date": r.date.isoformat() if r.date else None,
        "start_time": r.start_time, "end_time": r.end_time,
        "minutes": r.minutes,
        "hours": round((r.minutes or 0) / 60, 2),
        "students_count": r.students_count,
        "note": r.note,
    }

def _support_group_percent(db: Session, group_ids: list,
                           start: date, end: date):
    """Shu oyda o'tilgan guruhlarning o'rtacha test foizi.

    Har bir natija alohida sanaladi (guruh o'rtachasining o'rtachasi
    emas) — ko'p o'quvchili guruh ko'proq vazn oladi."""
    if not group_ids:
        return None
    rows = (db.query(models.ExamResult)
            .join(models.Exam,
                  models.ExamResult.exam_id == models.Exam.id)
            .filter(models.Exam.group_id.in_(group_ids),
                    models.Exam.date >= start,
                    models.Exam.date <= end,
                    models.ExamResult.percent.isnot(None),
                    models.ExamResult.absent == 0).all())
    vals = [r.percent for r in rows if r.percent is not None]
    return round(sum(vals) / len(vals), 1) if vals else None

def _support_month(db: Session, teacher_id: int, year: int,
                   month: int) -> dict:
    start, end = billing.month_bounds(year, month)
    rows = (db.query(models.SupportSession)
            .filter(models.SupportSession.teacher_id == teacher_id,
                    models.SupportSession.date >= start,
                    models.SupportSession.date <= end)
            .order_by(models.SupportSession.date,
                      models.SupportSession.id).all())
    hours = round(sum(r.minutes or 0 for r in rows) / 60, 2)
    students = sum(r.students_count or 0 for r in rows)
    gids = sorted({r.group_id for r in rows if r.group_id})
    pct = _support_group_percent(db, gids, start, end)
    calc = roles.support_salary(hours, students, pct)
    gnames = {g.id: g.name for g in db.query(models.Group)
              .filter(models.Group.id.in_(gids or [-1])).all()}
    return {
        "period": f"{year:04d}-{month:02d}",
        "sessions": [_support_session_out(db, r) for r in rows],
        "session_count": len(rows),
        "groups": [{"id": i, "name": gnames.get(i)} for i in gids],
        **calc,
        "formula": (f"({calc['hours']} soat x "
                    f"{roles.SUPPORT_HOURS_W} + {calc['students']} "
                    f"o'quvchi x {roles.SUPPORT_STUDENTS_W} + "
                    f"koef {calc['coef']} x {roles.SUPPORT_RESULT_W}) "
                    f"x {roles.SUPPORT_PAY_UNIT:,}".replace(",", " ")),
        "min": roles.SUPPORT_PAY_MIN,
        "max": roles.SUPPORT_PAY_MAX,
    }

def _time_to_min(t: str):
    try:
        h, m = t.strip().split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None

def _month_range(y: int, m: int):
    start = date(y, m, 1)
    end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return start, end

def _examiner_month(db: Session, user_id: int, y: int, m: int) -> dict:
    """Bitta examinerning bir oylik ball hisobi.

    Faqat O'TKAZILGAN (done) imtihonlar sanaladi — natijasi kiritilmagan
    imtihon hali ish emas. Ball: daraja bo'yicha baza + qatnashgan
    o'quvchi soni x koeffitsiyent. Jarimalar va qo'lda ayirilgan ballar
    ayirib tashlanadi, so'ng ball x 1 000 so'm (chegara 400k — 1.5M)."""
    start, end = _month_range(y, m)
    exams = (
        db.query(models.Exam)
        .filter(models.Exam.examiner_id == user_id,
                models.Exam.status == "done",
                models.Exam.date >= start, models.Exam.date < end)
        .order_by(models.Exam.date, models.Exam.id)
        .all()
    )
    rows, base_total, pen_total = [], 0.0, 0.0
    for e in exams:
        g = db.query(models.Group).get(e.group_id)
        students = len([r for r in e.results if not r.absent])
        pts = roles.examiner_exam_points(e.kind, g.level if g else None,
                                         students)
        pen = roles.examiner_penalty_points(
            e.kind, g.level if g else None,
            bool(e.penalty_lc_up), bool(e.penalty_coin),
            e.penalty_delay_hours or 0)
        row = {
            "exam_id": e.id,
            "date": e.date.isoformat(),
            "group": g.name if g else "—",
            "kind": roles.EXAM_KIND_LABELS.get(e.kind, e.kind),
            "retake": bool(e.retake_of_id),
            "students": students,
            "penalty_lc_up": bool(e.penalty_lc_up),
            "penalty_coin": bool(e.penalty_coin),
            "penalty_delay_hours": e.penalty_delay_hours or 0,
            "penalty_note": e.penalty_note,
            "penalty_points": pen,
        }
        if pts is None:
            # Mock jadvalda yo'q — ball bermaydi, lekin ro'yxatda
            # ko'rinadi (odam "qani mock'im" deb qidirmasin).
            row.update({"tier_label": "Jadvalda yo'q (mock)",
                        "base": 0, "per_student": 0, "points": 0.0})
        else:
            row.update({"tier_label": pts["tier_label"],
                        "base": pts["base"],
                        "per_student": pts["per_student"],
                        "points": pts["points"]})
            base_total += pts["points"]
        pen_total += pen
        rows.append(row)

    adjs = (
        db.query(models.ExaminerAdjustment)
        .filter(models.ExaminerAdjustment.user_id == user_id,
                models.ExaminerAdjustment.date >= start,
                models.ExaminerAdjustment.date < end)
        .order_by(models.ExaminerAdjustment.date,
                  models.ExaminerAdjustment.id)
        .all()
    )
    adj_total = round(sum(a.points or 0 for a in adjs), 2)
    net = round(base_total - pen_total - adj_total, 2)
    pay = roles.examiner_salary(net)
    return {
        "period": f"{y:04d}-{m:02d}",
        "exams": rows,
        "exam_count": len(rows),
        "base_points": round(base_total, 2),
        "penalty_points": round(pen_total, 2),
        "adjustments": [
            {"id": a.id, "date": a.date.isoformat(), "points": a.points,
             "reason": a.reason, "created_by": a.created_by}
            for a in adjs],
        "adjustment_points": adj_total,
        **pay,
        "table": [
            {"tier": k, "label": roles.EXAMINER_TIER_LABELS[k],
             "base": v[0], "per_student": v[1],
             "pen_lc_up": roles.EXAMINER_PENALTIES[k][0],
             "pen_coin": roles.EXAMINER_PENALTIES[k][1],
             "pen_hour": roles.EXAMINER_PENALTIES[k][2]}
            for k, v in roles.EXAMINER_EXAM_POINTS.items()],
        "hint": ("Har imtihon: daraja balli + o'quvchi soni x koeffitsiyent. "
                 "Jami ball x 1 000 so'm. Kamida 400 000, ko'pi bilan "
                 "1 500 000 so'm. Kamchilik uchun bo'lim boshliqlari ball "
                 "ayirishi mumkin."),
    }

def _ensure_month_charges(db: Session):
    """Har oyning 1-kuni ertalab 5:00 (Toshkent)dan boshlab faol
    o'quvchilardan shu oy to'lovi avtomat yechiladi.

    Server "uxlab" qolgan bo'lsa ham birinchi kirishda ishlaydi.
    Idempotent: allaqachon yechilgan o'quvchidan qayta yechilmaydi."""
    now = roles.local_now()
    today = now.date()
    if today.day == 1 and now.hour < 5:
        return
    period = f"{today.year:04d}-{today.month:02d}"
    # POYGA HIMOYASI: bir vaqtda ikki server nusxasi ishga tushsa,
    # ikkalasi ham "hali yechilmagan" deb o'ylab QAYTA yechmasin.
    # Postgres advisory lock tranzaksiya tugaguncha ushlab turadi;
    # SQLite (test) bitta jarayon bo'lgani uchun kerak emas.
    try:
        if db.get_bind().dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(917201)"))
    except Exception:
        pass
    done = db.query(models.Payment).filter(
        models.Payment.kind == "charge",
        models.Payment.period == period,
        models.Payment.created_by == "avtomat (oylik)").first()
    if done:
        return
    group_ids = [gid for (gid,) in
                 db.query(models.Student.group_id)
                 .filter(models.Student.status == "active",
                         models.Student.group_id.isnot(None))
                 .distinct().all()]
    n = 0
    for gid in group_ids:
        g = db.query(models.Group).get(gid)
        if not g:
            continue
        try:
            charges = billing.compute_student_charges(
                db, g, today.year, today.month)
        except Exception:
            continue
        for c in charges:
            if c.get("already_charged") or (c.get("amount") or 0) <= 0:
                continue
            if _charge_skipped(db, c["student_id"], period):
                continue
            db.add(models.Payment(
                student_id=c["student_id"],
                amount=-roles.money(abs(c["amount"])),
                kind="charge",
                note=f"{g.name} - {period} oyi uchun "
                     f"{c.get('billable_lessons', '')} dars (avtomat)",
                created_by="avtomat (oylik)",
                period=period,
            ))
            n += 1
    if n:
        db.commit()
    # Muzlatilganlardan bugun qaytishi kerak bo'lganlar bo'yicha
    # adminlarga Telegram eslatma yuborilmaydi (vazifa allaqachon
    # tushgan) — bu yerda faqat eski jurnal yozuvlarini tozalaymiz.
    try:
        old = datetime.utcnow() - timedelta(days=30)
        db.query(models.LoginAttempt).filter(
            models.LoginAttempt.created_at < old).delete()
        db.query(models.ErrorLog).filter(
            models.ErrorLog.created_at < old).delete()
        db.commit()
    except Exception:
        db.rollback()

def _founder_name_fix(db: Session):
    """Asoschi akkaunti "Administrator" deb nomlangan edi — markazda
    administrator deganda sotuv menejeri tushuniladi, chalkashadi."""
    f = db.query(models.User).filter(
        models.User.role == roles.FOUNDER,
        models.User.full_name == "Administrator").first()
    if f:
        f.full_name = "Asoschi"
        db.commit()

def _freeze_task(db, st: models.Student, until, note):
    days = max((until - roles.local_today()).days, 1) if until else 1
    body = (f"{st.full_name} muzlatildi."
            + (f" Qaytish sanasi: {until.isoformat()}." if until else "")
            + (f" Izoh: {note}" if note else "")
            + " Shu kuni o'quvchi bilan aloqaga chiqing.")
    _hr_task(db, title=f"Muzlatilgan o'quvchi: {st.full_name}",
             body=body, to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER],
             branch_id=st.branch_id, days=days, priority="high")




# ---------------------------------------------------------------------------
# SUPPORT BO'SHATILGANDA GURUHLARI BO'SHASIN (2026-08-10, Jahongir)
#
# Muammo: support teacher ishdan bo'shatilsa (yoki akkaunti o'chirilsa),
# support_assignments jadvalidagi yozuvlari joyida qolardi. Natijada
# guruh kartasida allaqachon ketgan xodim "support" bo'lib turardi va
# hech kim o'sha guruhga yangi support biriktirish kerakligini bilmasdi.
# Aynan shu Malika bilan bo'lgan: akkaunt o'chirilgan, ismi esa hamon
# guruhda.
#
# Yechim ikki qismli: (1) bo'shatish PAYTIDA biriktirishlarni olib
# tashlaymiz va support managerga vazifa qo'yamiz; (2) allaqachon
# qolib ketgan eski yozuvlarni bir marta tozalaymiz (pastdagi funksiya).
# ---------------------------------------------------------------------------
def _backfill_student_accounts(db) -> int:
    """BARCHA mavjud o'quvchilarga bir yo'la akkaunt ochadi (2026-08-10).

    Jahongir: "hop endi o'quvchilarga avtomat login parol qo'yib ber,
    loginga nomeri, parolga jonyjony."

    _ensure_student_account faqat YANGI kiritilgan (yoki tahrirlangan)
    o'quvchiga ishlaydi - bu funksiya esa undan OLDIN kiritilgan eski
    o'quvchilarni bir marta qoplab chiqadi. Har ishga tushishda
    tekshiriladi, lekin hisobi ochilganlar qayta ko'rilmaydi.

    TEZLIK: parol hammada bir xil (jonyjony) bo'lgani uchun hash BIR
    MARTA hisoblanadi. Aks holda bcrypt har o'quvchiga ~100ms olib,
    yuzlab o'quvchida serverning ishga tushishi o'zi qulab tushardi.
    Band username tekshiruvi ham bitta so'rov bilan (hammasi to'plamga
    olinadi) - N ta alohida so'rov emas.

    Qoidalar _ensure_student_account bilan BIR XIL: login = telefon
    (faqat raqamlar, kamida 7 ta), telefoni yo'q/band bo'lsa jimgina
    o'tkaziladi. Arxivdagi o'quvchiga hisob ochilmaydi. Telefonsizlar
    ro'yxati asoschiga bir martalik vazifa bo'lib tushadi - aks holda
    "nega bolam kira olmayapti" degan savol javobsiz qolardi."""
    from auth import hash_password

    rows = (db.query(models.Student)
            .filter(models.Student.user_id.is_(None),
                    models.Student.status.in_(("active", "trial",
                                               "frozen")))
            .order_by(models.Student.id).all())
    if not rows:
        return 0

    taken = {u for (u,) in db.query(models.User.username).all()}
    shared_hash = hash_password(roles.DEFAULT_PASSWORD)

    made, no_phone = 0, []
    for st in rows:
        raw = (st.phone or st.parent_phone or "")
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) < 7:
            no_phone.append(st)
            continue
        if digits in taken:
            continue
        u = models.User(
            username=digits,
            password_hash=shared_hash,
            full_name=st.full_name,
            role=roles.STUDENT,
            branch_id=st.branch_id,
            is_active=1,
        )
        db.add(u)
        db.flush()
        st.user_id = u.id
        taken.add(digits)
        made += 1
    db.commit()

    try:
        if no_phone:
            who = (db.query(models.User)
                   .filter(models.User.role == roles.FOUNDER,
                           models.User.is_active == 1).first())
            if who:
                names = [f"{x.full_name}"
                         + (f" ({x.public_id})" if x.public_id else "")
                         for x in no_phone[:80]]
                more = len(no_phone) - len(names)
                _hr_task_for(
                    db, who.id,
                    title="Telefonsiz o'quvchilar - akkaunt ochilmadi",
                    body=("Quyidagi o'quvchilarda telefon raqami "
                          "yo'qligi uchun Jony Student akkaunti "
                          "ochilmadi. Kartasiga raqam kiritilishi "
                          "bilan akkaunt avtomat ochiladi:\n\n- "
                          + "\n- ".join(names)
                          + (f"\n... va yana {more} ta" if more > 0
                             else "")),
                    days=5)
                db.commit()
    except Exception:
        db.rollback()
    return made


def _seed_done(db: Session, key: str) -> bool:
    """Og'ir seed allaqachon to'liq bajarilganmi - bitta yengil so'rov."""
    try:
        return db.query(models.SeedMark).get(key) is not None
    except Exception:
        return False


def _seed_mark(db: Session, key: str) -> None:
    """Seed to'liq bajarildi - keyingi startlarda ochilmasin."""
    try:
        if db.query(models.SeedMark).get(key) is None:
            db.add(models.SeedMark(key=key))
            db.commit()
    except Exception:
        db.rollback()


def _cleanup_frozen_absences(db: Session) -> int:
    """Muzlatilgan o'quvchilarning oxirgi ketma-ket "kelmadi"
    yozuvlarini o'chiradi - ustoz oyligidan chiqsin.

    Jahongir: "3ta dars kelmadi, avtomat muzlatasan degan edim, lekin
    shu 3ta yoq deb belgilangan davomatni olib tashlanishi kerak,
    chunki bu kelmaganlarga oylik hisoblanmasligi kerak ustozga".

    Yangi avtomuzlatishlarda bu yo'qlama saqlash paytida o'zi bo'ladi
    (groups_lessons.save_attendance ichida). Bu funksiya esa ESKI
    holatlarni tozalaydi: qoida qo'shilishidan oldin muzlatilganlar
    va qo'lda muzlatilganlar. Ehtiyot chorasi: faqat oxirgi KETMA-KET
    kelmagan zanjiri kamida 3 ta bo'lsa tegiladi - 1-2 ta qoldirib
    muzlatilgan (masalan oilaviy sabab) holatga aralashmaymiz.

    Yoqlamasi butunlay bo'shab qolgan dars "o'tilmagan" (held=0) ga
    qaytadi - xuddi avtomuzlatishdagi kabi. Idempotent: bir marta
    o'chirilgach zanjir topilmaydi."""
    frozen = (db.query(models.Student)
              .filter(models.Student.status == "frozen",
                      models.Student.group_id.isnot(None)).all())
    removed = 0
    for st in frozen:
        try:
            rows = (db.query(models.Attendance)
                    .join(models.Lesson,
                          models.Lesson.id == models.Attendance.lesson_id)
                    .filter(models.Attendance.student_id == st.id,
                            models.Lesson.group_id == st.group_id)
                    .order_by(models.Lesson.date.desc(),
                              models.Lesson.id.desc())
                    .limit(12).all())
            chain = []
            for a in rows:
                if (a.present or 0) != 0:
                    break
                chain.append(a)
            if len(chain) < 3:
                continue
            lesson_ids = [a.lesson_id for a in chain]
            for a in chain:
                db.delete(a)
            db.flush()
            for lid_ in lesson_ids:
                ls_ = db.query(models.Lesson).get(lid_)
                if ls_ and not db.query(models.Attendance).filter(
                        models.Attendance.lesson_id == lid_).count():
                    ls_.held = 0
            removed += len(chain)
            audit.log(db, None, entity="student", action="update",
                      entity_id=st.id, entity_label=st.full_name,
                      note=(f"Muzlatilgan o'quvchining {len(chain)} ta "
                            "'kelmadi' yo'qlamasi o'chirildi - ustoz "
                            "oyligiga kirmasin"), commit=False)
            db.commit()
        except Exception:
            db.rollback()
    return removed


def _support_manager_id(db: Session, branch_id=None):
    """Vazifa kimga tushsin: support boshlig'i -> o'quv bo'limi -> asoschi.

    Support boshlig'i bo'lmasa vazifa YO'QOLIB ketmasligi kerak, shuning
    uchun zanjir bo'ylab yuqoriga ko'tariladi."""
    for role in (roles.HEAD_SUPPORT, roles.ACADEMIC_HEAD, roles.FOUNDER):
        q = (db.query(models.User)
             .filter(models.User.role == role, models.User.is_active == 1))
        if branch_id:
            # avval o'sha filialdagisini qidiramiz
            row = q.filter(models.User.branch_id == branch_id).first()
            if row:
                return row.id
        row = q.first()
        if row:
            return row.id
    return None


def _release_support_groups(db: Session, target, reason: str) -> list:
    """Support bo'shatilganda guruhlarini bo'shatadi va vazifa yaratadi.

    Qaytaradi: bo'shab qolgan guruh nomlari ro'yxati."""
    rows = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.user_id == target.id).all())
    if not rows:
        return []

    gids = [r.group_id for r in rows if r.group_id]
    groups = (db.query(models.Group)
              .filter(models.Group.id.in_(gids or [-1]))
              .order_by(models.Group.name).all())
    names = [g.name for g in groups]

    for r in rows:
        db.delete(r)
    db.flush()

    # Vazifa yaratish ASOSIY ishni buzmasligi kerak - xodimni bo'shatish
    # baribir amalga oshsin, vazifada nimadir noto'g'ri ketsa ham.
    try:
        who = _support_manager_id(db, getattr(target, "branch_id", None))
        if who and names:
            _hr_task_for(
                db, who,
                title=(f"Supportsiz qolgan guruhlar: {target.full_name} "
                       f"({date.today().isoformat()})"),
                body=(f"{target.full_name} {reason}. Quyidagi guruhlar "
                      f"supportsiz qoldi - yangi support biriktirish "
                      f"kerak:\n\n- " + "\n- ".join(names) +
                      "\n\nGuruhlar bo'limidan har biriga support "
                      "tayinlang."),
                branch_id=getattr(target, "branch_id", None), days=2)
    except Exception:
        pass
    return names


def _cleanup_stale_support_assignments(db: Session) -> int:
    """Allaqachon qolib ketgan biriktirishlarni tozalaydi (bir martalik).

    Bu funksiya tuzatishdan OLDIN bo'shatilgan supportlar uchun - ular
    uchun yuqoridagi ilgak ishlamagan. Har ishga tushishda tekshiriladi,
    lekin tozalaydigan narsa bo'lmasa hech nima qilmaydi."""
    rows = db.query(models.SupportAssignment).all()
    if not rows:
        return 0
    uids = {r.user_id for r in rows if r.user_id}
    ok = {u.id for u in db.query(models.User)
          .filter(models.User.id.in_(uids or [-1]),
                  models.User.is_active == 1,
                  models.User.role == roles.SUPPORT_TEACHER).all()}
    stale = [r for r in rows if r.user_id not in ok]
    if not stale:
        return 0

    gids = [r.group_id for r in stale if r.group_id]
    names = [g.name for g in db.query(models.Group)
             .filter(models.Group.id.in_(gids or [-1]))
             .order_by(models.Group.name).all()]
    for r in stale:
        db.delete(r)
    db.commit()

    try:
        who = _support_manager_id(db)
        if who and names:
            _hr_task_for(
                db, who,
                title=f"Supportsiz qolgan guruhlar ({date.today().isoformat()})",
                body=("Ishdan bo'shatilgan yoki lavozimi o'zgargan "
                      "supportlarning guruhlari bo'shatildi. Quyidagi "
                      "guruhlarga yangi support biriktirish kerak:\n\n- "
                      + "\n- ".join(names)),
                days=3)
            db.commit()
    except Exception:
        db.rollback()
    return len(stale)


__all__ = [
    "_plan_fakt_revenue_plan",
    "_visible_discounts",
    "_balances_bulk", "_neg_since_bulk", "_aging_bucket",
    "DEBT_AGING_BUCKETS", "_risk_scan",
    "_discipline_stats", "_discipline_one", "_fmt_delay",
    "ATT_ONTIME_MIN",
    "_backfill_student_accounts",
    "_release_support_groups", "_cleanup_stale_support_assignments",
    "_support_manager_id",
    "GRID_END_MIN",
    "GRID_START_MIN",
    "PUBLIC_ID_PREFIX",
    "SCHEMA_STAMP",
    "_PERM_CACHE",
    "_activate_student",
    "_active_season",
    "_apply_reschedule",
    "_backfill_public_ids",
    "_book_out",
    "_branch_scope_ids",
    "_cabinet_groups",
    "_card",
    "_charge_from_activation",
    "_charge_skipped",
    "_check_enrolment",
    "_check_schedule",
    "_check_teacher_load",
    "_coin_balance",
    "_complaint_out",
    "_criteria",
    "_discount_alive",
    "_discount_out",
    "_drop_coin_entry",
    "_ensure_month_charges",
    "_ensure_new_columns",
    "_ensure_public_id",
    "_ensure_student_account",
    "_ensure_staff_date_tasks",
    "_ensure_teacher_card",
    "_exam_order_form",
    "_exam_order_out",
    "_exam_summary",
    "_examiner_month",
    "_expenses_total",
    "_expire_discounts",
    "_family_discount_percent",
    "_norm_surname",
    "_notify_discount_approvers",
    "_same_surname",
    "_do_family_link",
    "_founder_name_fix",
    "_fraud_alert",
    "_freeze_task",
    "_gam_card",
    "_in_user_branches",
    "_get_group_in_scope",
    "_grade_after",
    "_grade_card",
    "_grade_map",
    "_grade_row_out",
    "_grade_rows",
    "_grade_state",
    "_group_capacity",
    "_group_days",
    "_group_slot",
    "_group_students",
    "_homework_stats",
    "_hr_task",
    "_hr_task_for",
    "_hr_user",
    "_income_by_method",
    "_league_for",
    "_league_out",
    "_league_promotion_effects",
    "_leagues",
    "_lessons_left_in_month",
    "_link_teacher_accounts",
    "_make_public_id",
    "_make_smm_task",
    "_maybe_auto_activate",
    "_month_end",
    "_month_range",
    "_months_between",
    "_my_academic_cards",
    "_my_exam_cards",
    "_my_facility_cards",
    "_my_finance_cards",
    "_my_groups",
    "_my_hr_cards",
    "_my_marketing_cards",
    "_my_sales_cards",
    "_my_teacher_cards",
    "_observation_out",
    "_onboarding_rows",
    "_payroll_total",
    "_period_bounds",
    "_period_key",
    "_perm_overrides",
    "_problem",
    "_raise_if_blocked",
    "_recalc_gamification",
    "_resch_out",
    "_reschedule_usage",
    "_rule_cap_hit",
    "_salary_card",
    "_schema_bootstrap",
    "_seed_brand",
    "_seed_hr_structure",
    "_seed_kb",
    "_set_grade",
    "_shift_month",
    "_smm_achievement_task",
    "_smm_user",
    "_staff_date_task",
    "_staff_dates",
    "_student_coin_balance",
    "_student_discount_percent",
    "_student_gamification",
    "_level_for_points",
    "_skill_points",
    "_skills_card",
    "_student_of_user",
    "_student_payments",
    "_student_ranks",
    "_study_items",
    "_study_progress",
    "_support_assigned_groups",
    "_support_group_percent",
    "_support_month",
    "_support_session_out",
    "_sync_coin_entry",
    "_sync_group_rates",
    "_sync_student_left_date",
    "_sync_teacher_left_date",
    "_task_checklist",
    "_task_out",
    "_task_status",
    "_teacher_age",
    "_teacher_earned",
    "_teacher_exam_results",
    "_teacher_high_results",
    "_teacher_months",
    "_teacher_of_user",
    "_teacher_owns",
    "_teacher_paid",
    "_teacher_pass_rate",
    "_teacher_test_avg",
    "_time_to_min",
    "_trial_attendance",
    "_branch_in",
    "_user_branch_ids",
    "_user_roles",
    "_utc_window",
    "_xp_history",
    "_xp_rule",
    "award_xp",
    "backfill_missing_ids",
    "has_perm",
    "perms_for",
    "scope_to_branch",
    "student_balance",
    "to_student_out",
]


# =====================================================================
#  USTOZ INTIZOMI — yo'qlama QACHON va KIM tomonidan belgilangani
#  Jahongir (2026-08-12, LC UP hisobotini ko'rsatib): "mana shunaqa
#  statistika bizga ham kerak hisobotlar bo'limida — ustozning
#  intizomi. Intizom foizi ustoz kartasida ham, o'ziga ham ko'rinib
#  tursin: qancha kechikib yo'qlama qilyapti, qancha o'z vaqtida."
# =====================================================================
# O'z vaqtida = ustozning O'ZI dars boshlanishidan 60 daqiqa ichida
# (yoki o'sha kuni oldinroq) belgilagan. Menejer/administrator
# belgilagan dars ustoz uchun o'z vaqtida HISOBLANMAYDI.
ATT_ONTIME_MIN = 60


def _fmt_delay(minutes) -> str:
    """31 -> "31 daq", 140 -> "2.3 soat"."""
    if minutes is None:
        return "—"
    m = round(minutes)
    if m < 60:
        return f"{m} daq"
    return f"{round(m / 60, 1)} soat"


def _discipline_stats(db: Session, start: date, end: date,
                      branch_id: int | None = None,
                      teacher_id: int | None = None) -> list:
    """Har ustoz bo'yicha yo'qlama intizomi ([start, end) oralig'ida).

    Qaytadi: ro'yxat, har biri:
      teacher_id, name, marked (belgilangan darslar), self_marked,
      manager_marked, on_time, on_time_pct, avg_delay_min (faqat
      KECHIKKAN belgilashlar bo'yicha), avg_delay_label, unmarked
      (o'tib ketgan, umuman belgilanmagan darslar), state.
    """
    today = roles.local_today()
    q = (db.query(models.Lesson, models.Group)
         .join(models.Group, models.Lesson.group_id == models.Group.id)
         .filter(models.Lesson.date >= start, models.Lesson.date < end))
    if branch_id:
        q = q.filter(models.Group.branch_id == branch_id)
    lessons = q.all()

    def _tid(ls, g):
        return ls.teacher_id or g.teacher_id

    if teacher_id:
        lessons = [(ls, g) for ls, g in lessons
                   if _tid(ls, g) == teacher_id]

    held = [(ls, g) for ls, g in lessons if ls.held == 1]
    lids = [ls.id for ls, _ in held]

    # Har dars uchun BIRINCHI belgilash vaqti va kim belgilagani
    first: dict = {}
    if lids:
        CHUNK = 900
        for i in range(0, len(lids), CHUNK):
            rows = (db.query(models.Attendance.lesson_id,
                             models.Attendance.created_at,
                             models.Attendance.created_by)
                    .filter(models.Attendance.lesson_id
                            .in_(lids[i:i + CHUNK])).all())
            for lid, at, by in rows:
                if at is None:
                    continue
                cur = first.get(lid)
                if cur is None or at < cur[0]:
                    first[lid] = (at, by)

    tnames = {t.id: t.full_name for t in db.query(models.Teacher).all()}
    agg: dict = {}

    def _e(tid):
        if tid not in agg:
            agg[tid] = {"teacher_id": tid,
                        "name": tnames.get(tid, f"Ustoz #{tid}"),
                        "marked": 0, "self_marked": 0,
                        "manager_marked": 0, "on_time": 0,
                        "denom": 0, "delays": [], "unmarked": 0}
        return agg[tid]

    for ls, g in held:
        tid = _tid(ls, g)
        if not tid or ls.id not in first:
            continue
        e = _e(tid)
        e["marked"] += 1
        at_utc, by = first[ls.id]
        is_self = bool(by) and by == tnames.get(tid)
        if is_self:
            e["self_marked"] += 1
        else:
            e["manager_marked"] += 1
            e["denom"] += 1          # menejer belgilagani = kechikkan
            continue
        st_time = _group_slot(g)[0]
        st_min = roles.time_to_minutes(st_time) if st_time else None
        if st_min is None:
            continue                  # dars vaqti yo'q — o'lchab bo'lmaydi
        start_dt = datetime.combine(
            ls.date, dtime(st_min // 60, st_min % 60))
        delay = (roles.to_local(at_utc) - start_dt).total_seconds() / 60
        if delay < 0:
            delay = 0.0
        e["denom"] += 1
        if delay <= ATT_ONTIME_MIN:
            e["on_time"] += 1
        else:
            e["delays"].append(delay - 0)

    # O'tib ketgan, belgilanmagan darslar
    for ls, g in lessons:
        if ls.held == 0 and ls.date < today:
            tid = _tid(ls, g)
            if tid:
                _e(tid)["unmarked"] += 1

    rows = []
    for e in agg.values():
        denom = e.pop("denom")
        e["measured"] = denom
        delays = e.pop("delays")
        pct = round(e["on_time"] / denom * 100, 0) if denom else None
        avg_d = (sum(delays) / len(delays)) if delays else (
            0.0 if denom else None)
        e["on_time_pct"] = pct
        e["avg_delay_min"] = round(avg_d, 0) if avg_d is not None else None
        e["avg_delay_label"] = _fmt_delay(avg_d)
        e["problems"] = (denom - e["on_time"]) + e["unmarked"]
        e["state"] = (None if pct is None else
                      "good" if pct >= 90 else
                      "mid" if pct >= 70 else "bad")
        rows.append(e)

    rows.sort(key=lambda r: (r["on_time_pct"] is None,
                             -(r["on_time_pct"] or 0)))
    return rows


def _discipline_one(db: Session, teacher_id: int,
                    start: date, end: date) -> dict | None:
    rows = _discipline_stats(db, start, end, teacher_id=teacher_id)
    return rows[0] if rows else None


# =====================================================================
#  KETISH XAVFI AVTOMAT SKANERI (kuniga 1 marta)
#  Jahongir (2026-08-12): "davomati 2 hafta ketma-ket tushayotgan yoki
#  qarzdor bo'lib qolayotgan o'quvchini tizim o'zi 'ketish xavfi'
#  ro'yxatiga qo'shsin... bu narsa adminlarga qizil bayroq bo'lib
#  vazifa bo'lib tushsin".
# =====================================================================
def _risk_scan(db: Session) -> int:
    """Faol o'quvchilarni tekshiradi, xavf topsa RiskFlag + shu filial
    administratorlariga SHOSHILINCH vazifa ochadi. Takror ochmaydi:
    o'quvchida shu signal bo'yicha faol bayroq turgan bo'lsa - jim.

    Qoidalar:
      1) Davomat: oxirgi 14 kun foizi avvalgi 14 kundan kamida 10
         punktga past VA 70% dan past (har oynada >=4 belgi bo'lsa).
      2) Qarz: balans minusda va qarz bir oylik narxdan 20%+ ko'p.
    """
    today = roles.local_today()
    key = f"risk_scan_{today.isoformat()}"
    if _seed_done(db, key):
        return 0
    _seed_mark(db, key)          # parallel so'rovlar takror yurmasin
    db.commit()

    students = (db.query(models.Student)
                .filter(models.Student.status == "active").all())
    if not students:
        return 0
    sids = [s.id for s in students]

    # Davomat: oxirgi 28 kun, ikkiga bo'lib
    since = today - timedelta(days=28)
    mid = today - timedelta(days=14)
    att: dict = {}
    CHUNK = 900
    for i in range(0, len(sids), CHUNK):
        rows = (db.query(models.Attendance.student_id,
                         models.Lesson.date,
                         models.Attendance.present)
                .join(models.Lesson,
                      models.Attendance.lesson_id == models.Lesson.id)
                .filter(models.Attendance.student_id.in_(sids[i:i + CHUNK]),
                        models.Lesson.held == 1,
                        models.Lesson.date >= since).all())
        for sid, d, pr in rows:
            e = att.setdefault(sid, [0, 0, 0, 0])  # old_n, old_p, new_n, new_p
            if d < mid:
                e[0] += 1
                e[1] += 1 if pr else 0
            else:
                e[2] += 1
                e[3] += 1 if pr else 0

    balances = _balances_bulk(db, sids)
    fees = {g.id: (g.monthly_fee or 0) for g in db.query(models.Group).all()}

    open_flags = {(f.student_id, f.signal) for f in
                  db.query(models.RiskFlag)
                  .filter(models.RiskFlag.active == 1).all()}

    admins: dict = {}
    for u in (db.query(models.User)
              .filter(models.User.role == roles.ADMINISTRATOR,
                      models.User.is_active == 1).all()):
        admins.setdefault(u.branch_id, []).append(u)

    made = 0
    for s in students:
        alerts = []
        e = att.get(s.id)
        if e and e[0] >= 4 and e[2] >= 4:
            oldp = e[1] / e[0] * 100
            newp = e[3] / e[2] * 100
            if newp < oldp - 10 and newp < 70:
                alerts.append((
                    "absent_streak",
                    f"Davomati {round(oldp)}% dan {round(newp)}% ga "
                    f"tushdi (oxirgi 2 hafta / avvalgi 2 hafta)"))
        bal = balances.get(s.id, 0.0)
        fee = fees.get(s.group_id, 0.0) or 0.0
        if bal < 0 and fee and -bal >= fee * 1.2:
            alerts.append((
                "payment_late",
                f"Qarzi {round(-bal):,} so'm - bir oylik narxdan "
                f"({round(fee):,}) ko'p".replace(",", " ")))

        for sig, note in alerts:
            if (s.id, sig) in open_flags:
                continue
            db.add(models.RiskFlag(
                student_id=s.id, signal=sig, active=1,
                note="Avtomat: " + note, created_by="Tizim"))
            open_flags.add((s.id, sig))
            for adm in admins.get(s.branch_id, []):
                db.add(models.Task(
                    title=f"KETISH XAVFI: {s.full_name}",
                    description=(note + ". O'quvchi yoki ota-onasi "
                                 "bilan bog'lanib sababini aniqlang va "
                                 "natijani yozing."),
                    assignee_id=adm.id,
                    branch_id=s.branch_id,
                    deadline=today + timedelta(days=2),
                    priority="urgent",
                    source="risk",
                    created_by="Tizim (avtomat)"))
            made += 1
    if made:
        db.commit()
        try:
            audit.log(db, None, entity="student", action="risk_scan",
                      note=f"Avtomat skaner: {made} ta xavf bayrog'i "
                           f"qo'yildi", commit=True)
        except Exception:
            db.rollback()
    return made
