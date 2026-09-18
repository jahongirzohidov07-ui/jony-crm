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
from sqlalchemy import func, or_, select, text
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

def _ensure_new_columns(cols=None):
    """create_all() faqat yo'q jadvalni yaratadi - mavjud jadvalga yangi
    ustun qo'shmaydi. Shuning uchun keyin qo'shilgan ustunlarni shu yerda
    qo'lda qo'shamiz. Har safar ishga tushganda bajariladi, lekin ustun
    allaqachon bo'lsa xatolik e'tiborsiz qoldiriladi - ya'ni takror
    ishlatish xavfsiz."""
    from sqlalchemy import text

    statements = [
        # Ko'p tilli grammatika (2026-08-24)
        "ALTER TABLE grammar_questions ADD COLUMN language VARCHAR",
        "ALTER TABLE users ADD COLUMN exit_type VARCHAR",
        "ALTER TABLE users ADD COLUMN exit_reason VARCHAR",
        "ALTER TABLE users ADD COLUMN exit_date DATE",
        "ALTER TABLE exams ADD COLUMN status VARCHAR DEFAULT 'done'",
        "ALTER TABLE exams ADD COLUMN approved_by VARCHAR",
        "ALTER TABLE exams ADD COLUMN approved_at DATE",
        "ALTER TABLE exams ADD COLUMN retake_of_id INTEGER",
        "ALTER TABLE exams ADD COLUMN note TEXT",
        # O'tish balli (2026-09-10). Eski testlarda NULL qoladi —
        # ular avvalgi chegaralarda hisoblanaveradi, tarix o'zgarmaydi.
        "ALTER TABLE exams ADD COLUMN pass_percent FLOAT",
        # Online test natijasini examiner tasdiqlaydi (2026-09-18)
        "ALTER TABLE exam_online ADD COLUMN published_at TIMESTAMP",
        "ALTER TABLE exam_online ADD COLUMN published_by VARCHAR",
        # Eski imtihonlar allaqachon o'tkazilgan - ular "done".
        "UPDATE exams SET status = 'done' WHERE status IS NULL",
        "ALTER TABLE groups ADD COLUMN room_id INTEGER",
        "ALTER TABLE groups ADD COLUMN capacity INTEGER",
        "ALTER TABLE students ADD COLUMN public_id VARCHAR",
        "ALTER TABLE students ADD COLUMN parent_id INTEGER",
        "ALTER TABLE leads ADD COLUMN public_id VARCHAR",
        # Nomzod qaysi lavozimga va qaysi fandan (2026-08-15)
        "ALTER TABLE candidates ADD COLUMN position VARCHAR",
        "ALTER TABLE candidates ADD COLUMN subject VARCHAR",
        # Eski narx himoyasi (2026-08-15)
        "ALTER TABLE course_price_changes ADD COLUMN "
        "keep_old_for_active INTEGER DEFAULT 1",
        "ALTER TABLE course_price_changes ADD COLUMN "
        "locked_students INTEGER DEFAULT 0",
        "ALTER TABLE students ADD COLUMN locked_lesson_price FLOAT",
        "ALTER TABLE students ADD COLUMN locked_price_at TIMESTAMP",
        "ALTER TABLE students ADD COLUMN locked_price_note VARCHAR",
        # Hamkor filial va kurslar (2026-08-15)
        "ALTER TABLE branches ADD COLUMN is_partner INTEGER DEFAULT 0",
        "ALTER TABLE branches ADD COLUMN partner_note VARCHAR",
        "ALTER TABLE branches ADD COLUMN owner_percent FLOAT",
        "ALTER TABLE groups ADD COLUMN course_id INTEGER",
        "ALTER TABLE groups ADD COLUMN price_manual INTEGER DEFAULT 0",
        # Coinga chegirma sotib olish (2026-08-15)
        "ALTER TABLE rewards ADD COLUMN kind VARCHAR DEFAULT 'gift'",
        "ALTER TABLE rewards ADD COLUMN discount_percent FLOAT",
        "ALTER TABLE rewards ADD COLUMN discount_amount FLOAT",
        # Do'kon mahsuloti rasmi (2026-08-20, Jahongir: "o'sha
        # narsani rasmi bo'lishi kerak")
        "ALTER TABLE rewards ADD COLUMN image TEXT",
        "ALTER TABLE discounts ADD COLUMN period VARCHAR",
        "ALTER TABLE discounts ADD COLUMN applied_at TIMESTAMP",
        "UPDATE rewards SET kind = 'gift' WHERE kind IS NULL",
        # Ariza savollari qo'lda kiritishda ham (2026-08-15)
        # Ona tili (2026-08-16)
        "ALTER TABLE candidates ADD COLUMN native_language VARCHAR",
        # Maqsad balli (2026-08-18)
        "ALTER TABLE student_gamification ADD COLUMN xp_target FLOAT",
        # Maqsad IELTS balli (2026-08-18, keyinroq: "nechi XP emas
        # IELTS nechi olmoqchiligi bolishi kerak")
        "ALTER TABLE student_gamification ADD COLUMN ielts_target FLOAT",
        "ALTER TABLE student_gamification ADD COLUMN study_hours_per_day INTEGER",
        # Darsni bekor qilish / dam kunlari (2026-08-19)
        "ALTER TABLE lessons ADD COLUMN cancelled INTEGER",
        "ALTER TABLE lessons ADD COLUMN cancel_note VARCHAR",
        # 2026-08-20: avtomat dam qoidasi avval avgustdan yoqilgan edi;
        # Jahongir "sentabrdan qilaver keyingi o'quv yilidan" dedi —
        # oradagi qisqa vaqtda avtomat bekor bo'lib qolgan avgust
        # darslari qaytariladi (qo'lda bekor qilinganlarga tegilmaydi,
        # ular izohidan ajratiladi).
        "UPDATE lessons SET cancelled=0, cancel_note=NULL "
        "WHERE cancel_note='Dam: avgustda 12 ta dars qoidasi' "
        "AND date < '2026-09-01'",
        # Liga coin shkalasi (2026-08-20, Jahongir tartibi:
        # "1,2,3,4,5,6,8,10,12,14,16,18,20,25,30" - 13 ko'tarilishga
        # joylashtirildi, cho'qqiga 25 va 30). Berilib bo'lgan
        # coinlarga tegilmaydi - faqat keyingi ko'tarilishlar yangi
        # shkalada.
        "UPDATE xp_leagues SET reward_coin=1 WHERE key='amateur'",
        "UPDATE xp_leagues SET reward_coin=2 WHERE key='wood'",
        "UPDATE xp_leagues SET reward_coin=3 WHERE key='stone'",
        "UPDATE xp_leagues SET reward_coin=4 WHERE key='bronze'",
        "UPDATE xp_leagues SET reward_coin=5 WHERE key='silver'",
        "UPDATE xp_leagues SET reward_coin=6 WHERE key='gold'",
        "UPDATE xp_leagues SET reward_coin=8 WHERE key='crystal'",
        "UPDATE xp_leagues SET reward_coin=10 WHERE key='elite'",
        "UPDATE xp_leagues SET reward_coin=12 WHERE key='master'",
        "UPDATE xp_leagues SET reward_coin=14 WHERE key='titan'",
        "UPDATE xp_leagues SET reward_coin=16 WHERE key='champion'",
        "UPDATE xp_leagues SET reward_coin=25 WHERE key='legendary'",
        "UPDATE xp_leagues SET reward_coin=30 WHERE key='goat'",
        "ALTER TABLE candidates ADD COLUMN address VARCHAR",
        "ALTER TABLE candidates ADD COLUMN birth_date_text VARCHAR",
        "ALTER TABLE candidates ADD COLUMN education VARCHAR",
        "ALTER TABLE candidates ADD COLUMN marital VARCHAR",
        "ALTER TABLE candidates ADD COLUMN socials VARCHAR",
        "ALTER TABLE candidates ADD COLUMN work_duration VARCHAR",
        "ALTER TABLE groups ADD COLUMN public_id VARCHAR",
        "ALTER TABLE payments ADD COLUMN public_id VARCHAR",
        # Dubl to'lovga qarshi idempotentlik kaliti (2026-08-14)
        "ALTER TABLE payments ADD COLUMN client_key VARCHAR",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_client_key "
        "ON payments (client_key)",
        "ALTER TABLE users ADD COLUMN public_id VARCHAR",
        # Xodim Telegrami (2026-08-15): xato ogohlantirishi va zaxira
        "ALTER TABLE users ADD COLUMN tg_code VARCHAR",
        "ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR",
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
        # Ustozga berilgan pul qaysi filialdan (2026-09-16)
        "ALTER TABLE teacher_payments ADD COLUMN branch_id INTEGER",
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
    # 2026-09-11 — TEZLIK. Bu ro'yxat 199 ta gapga yetdi va har biri
    # bazaga alohida borib kelardi. Ustunlarning deyarli hammasi
    # allaqachon mavjud, ya'ni 199 ta so'rovning 199 tasi ham
    # "xato, e'tiborsiz qoldirildi" bilan tugardi. Neon'da bu ~6
    # soniya — sxema o'zgargan deployda birinchi so'rov shu sababdan
    # ham 30 soniyalik chegaraga yaqinlashardi.
    #
    # Endi bazadagi ustunlar BITTA so'rov bilan olinadi va mavjud
    # ustunni qo'shishga urinilmaydi. Natija aynan bir xil, faqat
    # ancha tez. UPDATE gaplari avvalgidek bajariladi.
    import re as _re_ens
    _add_rx = _re_ens.compile(
        r'^\s*ALTER\s+TABLE\s+"?([A-Za-z0-9_]+)"?\s+ADD\s+COLUMN\s+'
        r'"?([A-Za-z0-9_]+)"?', _re_ens.I)
    try:
        _have = cols if cols is not None else _db_columns_map()
    except Exception:
        _have = {}
    _skipped = 0
    for stmt in statements:
        m = _add_rx.match(stmt)
        if m and m.group(2) in _have.get(m.group(1), set()):
            _skipped += 1
            continue
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            pass
    if _skipped:
        print("[schema] mavjud ustunlar o'tkazib yuborildi: %d" % _skipped)

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

            # O'TISH BALLI (2026-09-10, Jahongir: "test turi boyivha
            # sozlamalarda bir marta ... 65% unit testda 60% esa mid
            # va end courselarda"). Bir marta seed qilinadi; keyin
            # asoschi o'zgartirsa, qayta yozib yuborilmaydi.
            # Jadval albatta mavjud bo'lsin: yangi jadval faqat
            # create_all bilan yaratiladi, migratsiya bilan emas.
            try:
                models.ExamPassRule.__table__.create(bind=engine,
                                                     checkfirst=True)
            except Exception:
                pass
            _have_pass = {r.kind for r in
                          db.query(models.ExamPassRule).all()}
            if not _have_pass:
                for _k, _p in roles.DEFAULT_EXAM_PASS.items():
                    db.add(models.ExamPassRule(kind=_k, percent=_p))
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
    "payment_fix": "TUZ",
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

# ---------------------------------------------------------------
#  SXEMA SHTAMPI
#
#  Sovuq start tez bo'lishi uchun jadval va ustunlar HAR SAFAR
#  tekshirilmaydi: bazada shu shtamp yozuvi bo'lsa, sxema "tayyor"
#  deb hisoblanadi va migratsiyalar UMUMAN ishlamaydi.
#
#  2026-08-28 — SHU YERDA JIDDIY XATO BO'LDI. Kontent-plan uchun
#  0010 migratsiyasi qo'shildi, lekin shtamp qo'lda yangilanmadi.
#  Natijada jonli bazada yangi ustunlar yaratilmadi va contents
#  jadvaliga har qanday so'rov "no such column: contents.proof"
#  bilan yiqildi — butun SMM bo'limi ochilmay qoldi.
#
#  Shuning uchun shtamp endi QO'LDA yozilmaydi: u oxirgi
#  migratsiya nomidan avtomat quriladi. Yangi migratsiya
#  qo'shilishi bilan shtamp o'zi o'zgaradi va migratsiyalar
#  albatta ishga tushadi. Odam esdan chiqarishi mumkin, kod yo'q.
#
#  _STAMP_MANUAL faqat MIGRATSIYASIZ o'zgarish uchun (masalan
#  yangi JADVAL qo'shilsa — uni create_all yaratadi, migratsiya
#  kerak emas). Shunda shu sanani yangilash kifoya.
# ---------------------------------------------------------------
#  2026-09-10 — AYNAN SHU XATO QAYTARILDI. "O'tish balli" ishida
#  yangi JADVAL (exam_pass_rules) va yangi USTUN (exams.pass_percent)
#  qo'shildi, lekin migratsiya yozilmagani uchun shtamp o'zgarmadi.
#  Natijada jonli bazada ular yaratilmadi va imtihonga tegadigan har
#  qanday so'rov yiqildi. Shtamp sanasi shuning uchun ko'tarildi.
#
#  2026-09-10 (KECHQURUN) — SHTAMP ENDI ODAMGA BOG'LIQ EMAS.
#  Yuqoridagi ikki avariya bir xil sababdan bo'ldi: shtamp faqat
#  MIGRATSIYA nomiga bog'langan edi, migratsiyasiz o'zgarish (yangi
#  jadval yoki ALTER bilan qo'shilgan ustun) esa uni qimirlatmasdi
#  va odam _STAMP_MANUAL ni yangilashni unutardi.
#
#  Endi shtampga MODEL BARMOQ IZI qo'shiladi: hamma jadval va ustun
#  nomlaridan hisoblangan qisqa xesh. Modelga bitta ustun qo'shilsa
#  xesh o'zi o'zgaradi -> shtamp o'zgaradi -> migratsiya va
#  create_all albatta ishlaydi. Unutish imkoni yo'q.
#
#  Barmoq izi FAQAT nomlardan olinadi (tur, uzunlik, tartib emas) —
#  ular bazaning haqiqiy holatini belgilaydi va SQLite/Postgres da
#  bir xil chiqadi, ya'ni har deployda bekorga o'zgarib ketmaydi.
# 2026-09-11 — ko'tarildi: placement_sessions.sec / sec_state
# ustunlari jonli bazaga qo'shilmay qolgan edi (seal_schema izohiga
# qarang). Shtamp ko'tarilmasa, tuzatish jonli bazaga yetib bormasdi.
_STAMP_MANUAL = "2026_09_11"
_STAMP_BASE = "stamp_%s_%s" % (
    _STAMP_MANUAL,
    migrations.MIGRATIONS[-1][0] if migrations.MIGRATIONS else "0")

_STAMP_CACHE: dict = {"v": None}


#  MUHIM: barmoq izi Base.metadata dan OLINMAYDI. Sabab —
#  jadvallar faqat models.py da emas, entry.py / guide.py /
#  level_test.py da ham e'lon qilingan. Vercel'da har fayl alohida
#  funksiya bo'lgani uchun metadata'da nechta jadval borligi qaysi
#  modul import qilinganiga qarab 154 ham, 167 ham bo'ladi. U holda
#  ikki funksiya ikki xil shtamp hisoblab, bir-birining shtampini
#  "eski" deb bilib, HAR sovuq startda to'liq bootstrap yugurtirardi
#  (aynan biz qochayotgan Neon trafigi).
#
#  Shuning uchun xesh MANBA FAYLLARDAN olinadi: papkadagi har bir
#  .py fayl ichida `__tablename__` bo'lsa — o'shandan jadval nomlari
#  va ustun nomlari regex bilan sug'urib olinadi. Natija import
#  tartibiga umuman bog'liq emas, va yangi model fayli qo'shilsa
#  o'zi topiladi. Izoh/route o'zgarishi xeshga ta'sir qilmaydi.
#  2026-09-11 — TAXALLUSLI IMPORT TUZATILDI.
#  entry.py ustunlarni `Column` deb emas, `_ptC` deb e'lon qiladi:
#      from sqlalchemy import Column as _ptC, Integer as _ptI
#      sec = _ptC(_ptS)
#  Oldingi regex faqat "Column(" ni qidirgani uchun entry.py dagi
#  YANGI USTUNLARNI UMUMAN KO'RMASDI — ya'ni shtamp qimirlamasdi va
#  biz endigina yopgan teshik qaytadan ochilib qolardi.
#  Endi har fayl uchun Column'ning taxalluslari import qatorlaridan
#  topib olinadi. test_schema_all_tables.py bu narsani ALOHIDA
#  tekshiradi: modeldagi har bir ustun barmoq iziga tushganmi.
def _model_column_aliases(data: bytes) -> list:
    import re as _re
    out = ["Column"]
    for m in _re.finditer(rb'\bColumn\s+as\s+([A-Za-z_][A-Za-z0-9_]*)',
                          data):
        out.append(m.group(1).decode("ascii"))
    return sorted(set(out), key=len, reverse=True)


def _model_signature_tokens() -> list:
    """Model fayllaridagi jadval va ustun nomlari (tartibi bilan)."""
    import re as _re
    d = os.path.dirname(os.path.abspath(__file__))
    out = []
    try:
        names = sorted(os.listdir(d))
    except Exception:
        return out
    for n in names:
        if not n.endswith(".py") or n.startswith("test_"):
            continue
        try:
            with open(os.path.join(d, n), "rb") as f:
                data = f.read()
        except Exception:
            continue
        if b"__tablename__" not in data:
            continue
        alt = b"|".join(_re.escape(a.encode("ascii"))
                        for a in _model_column_aliases(data))
        rx = _re.compile(
            rb'^[ \t]*(?:__tablename__[ \t]*=[ \t]*["\']([A-Za-z0-9_]+)'
            rb'|([A-Za-z0-9_]+)[ \t]*=[ \t]*'
            rb'(?:[A-Za-z_][A-Za-z0-9_]*\.)?(?:' + alt + rb')\()',
            _re.M)
        out.append(n)
        for m in rx.finditer(data):
            out.append((m.group(1) or m.group(2) or b"").decode("utf-8"))
    return out


def _model_signature_bytes() -> bytes:
    return "|".join(_model_signature_tokens()).encode("utf-8")


def models_fingerprint() -> str:
    """Model sxemasining qisqa, barqaror xeshi.

    Import tartibiga bog'liq emas: manba fayllardan o'qiladi."""
    import hashlib
    return hashlib.sha1(_model_signature_bytes()).hexdigest()[:10]


def schema_stamp() -> str:
    """Joriy sxema shtampi. Bir jarayonda bir marta hisoblanadi."""
    if _STAMP_CACHE["v"] is None:
        _STAMP_CACHE["v"] = _STAMP_BASE + "_" + models_fingerprint()
    return _STAMP_CACHE["v"]


# Eski nom — tashqi kod va testlar uchun qoldirildi.
SCHEMA_STAMP = _STAMP_BASE

# ---------------------------------------------------------------
#  SOVUQ START TEZLIGI  (2026-08-14, Jahongir: "Har sovuq startda
#  143 ta jadval uchun create_all reflection so'rovlari ketadi ...
#  shularni ham togrla")
#
#  Ilgari server har uyg'onganda Base.metadata.create_all() ishlar
#  edi. U 143 ta jadvalning HAR BIRI uchun bazadan "bu jadval
#  bormi?" deb so'rardi — ya'ni bitta bo'sh so'rov o'rniga 143 ta.
#  Vercel'da funksiya tez-tez uxlab-uyg'onadi, natijada Neon
#  trafigi bekorga sarflanardi (avgustdagi kvota avariyasi).
#
#  Endi BITTA yengil so'rov qilinadi: schema_migrations jadvalida
#  joriy SCHEMA_STAMP bormi? Bo'lsa — sxema tayyor, hech qanday
#  reflection ham, migratsiya ham ishlamaydi. Yo'q bo'lsa (yangi
#  baza yoki yangi migratsiya) — avvalgidek to'liq yo'l bosiladi
#  va oxirida stamp yoziladi.
# ---------------------------------------------------------------

_SCHEMA_OK: bool | None = None
# Jarayon BOSHLANGANDA sxema tayyor edimi? _schema_bootstrap() ishlagach
# _SCHEMA_OK True bo'ladi, lekin entry.py'da KEYIN e'lon qilinadigan
# jadvallar hali yaratilmagan bo'lishi mumkin — shuning uchun
# ensure_tables() aynan SHU bayroqqa qaraydi.
_SCHEMA_BOOT_OK: bool = False


def _schema_ready() -> bool:
    """Sxema joriy versiyada tayyormi? Javob jarayon xotirasida
    saqlanadi — bitta funksiya nusxasi ichida faqat bir marta
    so'raladi."""
    global _SCHEMA_OK
    if _SCHEMA_OK is not None:
        return _SCHEMA_OK
    from sqlalchemy import text
    ok = False
    db = None
    try:
        db = SessionLocal()
        row = db.execute(
            text("SELECT 1 FROM schema_migrations "
                 "WHERE version = :v LIMIT 1"),
            {"v": schema_stamp()}).first()
        ok = row is not None
    except Exception:
        # Jadval hali yo'q (yangi baza) yoki baza javob bermadi —
        # ehtiyot yuzasidan to'liq yo'ldan boramiz.
        ok = False
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
    global _SCHEMA_BOOT_OK
    _SCHEMA_OK = ok
    _SCHEMA_BOOT_OK = ok
    return ok


#  AVTOMAT USTUN QO'SHISH (2026-09-10)
#
#  Ilgari yangi ustun qo'shilsa, uni QO'LDA _ensure_new_columns()
#  ro'yxatiga ALTER qatori qilib yozish kerak edi. Odam unutsa —
#  jonli bazada ustun paydo bo'lmasdi va o'sha jadvalga tegadigan
#  har qanday so'rov 500 qaytarardi (28-avgust: contents.proof,
#  10-sentabr: exams.pass_percent).
#
#  Endi kod modeldagi ustunlarni bazadagilar bilan o'zi solishtiradi
#  va yetishmayotganini o'zi qo'shadi. Faqat SEKIN yo'lda (shtamp
#  o'zgarganda) ishlaydi, ya'ni har sovuq startda emas — Neon
#  trafigiga ta'siri yo'q.
#
#  Ustun ataylab NULL bo'ladigan qilib qo'shiladi: mavjud qatorlarda
#  qiymat yo'q, NOT NULL qo'yilsa ALTER yiqilardi. Ma'lumot
#  o'chirilmaydi, faqat qo'shiladi.
def _db_columns_map() -> dict:
    """Bazadagi hamma jadval va ustun nomlari.

    Postgres'da BITTA so'rov bilan olinadi. Jadval-jadval
    so'rasak 167 ta borib-kelish bo'lardi — sovuq startni
    og'irlashtiradi va aynan shu narsadan qochyapmiz."""
    out: dict = {}
    try:
        if engine.dialect.name == "postgresql":
            with engine.connect() as cx:
                rows = cx.execute(text(
                    "SELECT table_name, column_name "
                    "FROM information_schema.columns "
                    "WHERE table_schema = current_schema()")).all()
            for tname, cname in rows:
                out.setdefault(tname, set()).add(cname)
            return out
        from sqlalchemy import inspect as _sa_inspect
        insp = _sa_inspect(engine)
        for tname in insp.get_table_names():
            try:
                out[tname] = {c["name"] for c in insp.get_columns(tname)}
            except Exception:
                pass
    except Exception:
        return out
    return out


def _auto_add_missing_columns(tables=None) -> list:
    added: list = []
    have_map = _db_columns_map()
    if not have_map:
        return added
    if tables is None:
        items = list(Base.metadata.tables.values())
    else:
        items = list(tables)
    q = engine.dialect.identifier_preparer.quote
    for table in items:
        tname = getattr(table, "name", None)
        if not tname or tname not in have_map:
            continue
        have = have_map[tname]
        for col in table.columns:
            if col.name in have:
                continue
            try:
                ddl = col.type.compile(dialect=engine.dialect)
            except Exception:
                continue
            sql = "ALTER TABLE %s ADD COLUMN %s %s" % (
                q(tname), q(col.name), ddl)
            try:
                with engine.begin() as cx:
                    cx.execute(text(sql))
                added.append(tname + "." + col.name)
            except Exception:
                pass
    if added:
        print("[schema] avtomat qo'shilgan ustunlar: " + ", ".join(added))
    return added


def _create_missing_tables(tables=None, cols=None) -> list:
    """Yetishmayotgan jadvallarni yaratadi.

    MUHIM: create_all() ni butun metadata ustidan chaqirmaymiz —
    u 167 ta jadvalning HAR BIRI uchun bazadan alohida "bu jadval
    bormi?" deb so'raydi, ya'ni 167 marta Neon'ga borib keladi.
    Sxema o'zgargan deploydan keyin birinchi so'rov shuning uchun
    30 soniyalik chegaradan oshib 500 qaytarardi (11-sentabr:
    ~3 daqiqa davomida foydalanuvchilar xato ko'rdi).

    Endi bazadagi jadvallar ro'yxati BITTA so'rov bilan olinadi va
    faqat yo'qlari yaratiladi — odatda bittasi ham yo'q."""
    items = (list(Base.metadata.tables.values()) if tables is None
             else list(tables))
    try:
        have = set((cols if cols is not None
                    else _db_columns_map()).keys())
    except Exception:
        have = None
    try:
        if have is None:
            Base.metadata.create_all(bind=engine, tables=items)
            return []
        need = [t for t in items if getattr(t, "name", None) not in have]
        if need:
            Base.metadata.create_all(bind=engine, tables=need)
            names = sorted(t.name for t in need)
            if len(names) <= 12:
                print("[schema] yangi jadval: " + ", ".join(names))
            else:
                print("[schema] yangi jadval: %d ta" % len(names))
        return need
    except Exception:
        try:
            Base.metadata.create_all(bind=engine, tables=items)
        except Exception:
            pass
        return []


def ensure_tables(tables):
    """Kichik yordamchi: sxema tayyor bo'lsa hech nima qilmaydi.
    entry.py'dagi "yangi jadval qo'shish" bloklari shuni chaqiradi —
    aks holda har cold start'da har bir jadval uchun alohida
    tekshiruv so'rovi ketardi."""
    if _schema_ready() and _SCHEMA_BOOT_OK:
        return
    tables = list(tables)
    _create_missing_tables(tables)
    # Jadval allaqachon bor, lekin unga yangi ustun qo'shilgan
    # bo'lsa — create_all buni sezmaydi, shuning uchun alohida.
    try:
        _auto_add_missing_columns(tables)
    except Exception:
        pass

_SCHEMA_PENDING: bool = False


def seal_schema() -> bool:
    """Sxema tekshiruvini YAKUNLAB, shtampni yozadi.

    entry.py o'z jadvallarini (placement_sessions, library_items,
    pd_videos va b.) e'lon qilib bo'lgach chaqiriladi. Shundagina
    Base.metadata TO'LIQ bo'ladi va yetishmayotgan jadval/ustunlar
    haqiqatan ham topiladi.

    11-sentabrdagi avariya aynan shu sababdan edi: bootstrap
    main.py import paytida ishlab, shtampni yozib qo'yardi; entry.py
    jadvallari esa keyin e'lon qilinardi va ularning yangi ustunlari
    hech qachon qo'shilmasdi."""
    global _SCHEMA_PENDING, _SCHEMA_OK
    if not _SCHEMA_PENDING:
        return False
    _SCHEMA_PENDING = False
    try:
        _create_missing_tables()
    except Exception:
        pass
    try:
        _auto_add_missing_columns()
    except Exception:
        pass
    db = SessionLocal()
    try:
        db.add(models.SchemaMigration(version=schema_stamp()))
        db.commit()
        _SCHEMA_OK = True
        print("[schema] shtamp yozildi: " + schema_stamp())
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return False
    finally:
        db.close()


def _schema_bootstrap():
    global _SCHEMA_OK
    if _schema_ready():
        return
    db = SessionLocal()
    try:
        try:
            done = db.query(models.SchemaMigration).filter(
                models.SchemaMigration.version == schema_stamp()).first()
        except Exception:
            done = None
        if done:
            _SCHEMA_OK = True
            return
        # TARTIB MUHIM: avval jadvallar, keyin migratsiyalar.
        # Migratsiyalar mavjud jadvallar ustida ishlaydi — bo'sh
        # bazada ular yiqilsa, quyidagi qadamlarga umuman
        # yetib borilmasdi.
        #
        # Bazadagi ustunlar xaritasi BIR MARTA olinadi va ikkala
        # qadamga uzatiladi — Postgres'da bu bitta so'rov.
        try:
            _cols = _db_columns_map()
        except Exception:
            _cols = None
        _made = _create_missing_tables(cols=_cols)
        if _made:
            _cols = None            # yangi jadvallar qo'shildi
        _ensure_new_columns(cols=_cols)
        _backfill_public_ids()
        migrations.run(db)
        # Mavjud jadvalga qo'shilgan yangi ustunlarni create_all
        # ko'rmaydi — ularni o'zimiz solishtirib qo'shamiz. Shu
        # bilan "migratsiya yozishni unutdim" xatosi tugaydi.
        try:
            _auto_add_missing_columns()
        except Exception:
            pass
        # SHTAMP SHU YERDA YOZILMAYDI — seal_schema() yozadi.
        #
        # 2026-09-11 (avariya): placement_sessions jadvali entry.py da
        # e'lon qilinadi, ya'ni main.py import bo'layotganda u hali
        # Base.metadata da YO'Q. Shu sababli yangi ustunlar (sec,
        # sec_state) jonli bazaga qo'shilmay qoldi va Lidlar sahifasi
        # 500 qaytardi. Shtampni esa bootstrap yozib qo'ygani uchun
        # keyingi urinishlar ham "hammasi joyida" deb o'tib ketardi.
        #
        # Endi shtamp faqat entry.py o'z jadvallarini e'lon qilib
        # bo'lgach yoziladi — ya'ni tekshiruv TO'LIQ modelda o'tadi.
        global _SCHEMA_PENDING
        _SCHEMA_PENDING = True
        _SCHEMA_OK = True
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
    digits, variants = roles.phone_login(s.phone or s.parent_phone)
    if not digits:
        return None
    # Ikkala ko'rinish ham tekshiriladi: 901234567 va 998901234567 —
    # bir o'quvchiga ikkinchi hisob ochilmasin (2026-09-16)
    if db.query(models.User).filter(
            models.User.username.in_(variants)).first():
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
    # 2026-08-25 TUZATISH. Jahongir: "ustoz lavozimiga otsa manager
    # lavozimi yoqolib qolibdi kira olmayabdi ekan".
    #
    # SABAB: lavozim almashtirilganda auth.py so'rov davomida
    # user.role ni tanlangan lavozimga o'zgartiradi (asosiysi
    # _primary_role ga saqlanadi). Bu yerda esa ro'yxat FAQAT
    # user.role dan boshlanardi — ya'ni ustozga o'tgan zahoti
    # asosiy lavozim (manager/filial rahbari) ro'yxatdan tushib
    # qolardi. Natijada ekrandagi tanlagich yo'qolib, xodim
    # ustoz kabinetida qamalib qolardi.
    #
    # Endi ro'yxat ASOSIY lavozimdan boshlanadi va tanlangani ham
    # albatta qo'shiladi — qaysi lavozimda turgan bo'lsa ham ro'yxat
    # to'liq qoladi.
    out = []
    prim = getattr(user, "_primary_role", None)
    if prim and prim in roles.ALL_ROLES:
        out.append(prim)
    if user.role and user.role not in out:
        out.append(user.role)
    try:
        for ur in (db.query(models.UserRole)
                   .filter(models.UserRole.user_id == user.id).all()):
            if ur.role and ur.role not in out and ur.role in roles.ALL_ROLES:
                out.append(ur.role)
    except Exception:
        pass
    user._all_roles = out
    return out


def _get_student_in_scope(db, student_id: int, user: models.User):
    """O'quvchini FILIAL CHEGARASI bilan oladi (2026-09-06 auditi).

    Ilgari o'quvchiga oid amallar (to'lov kiritish, muzlatish,
    faollashtirish, coin, qarz eslatmasi...) faqat rolni tekshirardi:
    filial admini boshqa filial o'quvchisining ID sini yozib ish
    ko'rishi mumkin edi. Guruhlar uchun bunday qorovul allaqachon bor
    edi (_get_group_in_scope) — endi o'quvchilar uchun ham bitta joyda.

    Filialsiz o'quvchi (endi kiritilgan) hammaga ochiq — null_ok=True."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    return s


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


_PARTNER_IDS: list | None = None


def partner_branch_ids(db) -> list:
    """HAMKOR filiallar ro'yxati (2026-08-15, Jahongir: "hamkorlikda
    ochgan Stech ... uni men umuman boshqarmayman, faqat asoschi
    sifatida 40% ulushim bor").

    Bunday filial JonyOS ichida to'liq ishlaydi, lekin uning raqamlari
    Jony Academy'ning UMUMIY yig'indilariga qo'shilmaydi. Ko'rish
    uchun tepadagi tanlagichdan o'sha filialni tanlash kerak.

    Javob jarayon xotirasida saqlanadi — har so'rovda qayta
    so'ralmasin (filial kam va deyarli o'zgarmaydi)."""
    global _PARTNER_IDS
    if _PARTNER_IDS is None:
        try:
            _PARTNER_IDS = [b.id for b in db.query(models.Branch)
                            .filter(models.Branch.is_partner == 1).all()]
        except Exception:
            return []
    return _PARTNER_IDS


_TEST_IDS = None


def test_branch_ids(db) -> list:
    """MASHQ (test) filiallari.

    2026-08-27, Jahongir: "marhaboga test filial, Stech korsatmasin".

    Test filiali xodimlarni o'rgatish uchun ochilgan — unda soxta
    o'quvchi va soxta lid bor. Uning raqamlari hisobotga tushsa,
    real ko'rsatkich buziladi.

    Belgisi NOM bo'yicha aniqlanadi ("Test" bilan boshlanadi) —
    tizimda allaqachon shu qoida ishlatilgan (leads.py, ochiq
    filial ro'yxati). Keyinchalik alohida ustun kerak bo'lsa,
    faqat SHU funksiya o'zgaradi."""
    global _TEST_IDS
    if _TEST_IDS is None:
        try:
            _TEST_IDS = [b.id for b in db.query(models.Branch).all()
                         if (b.name or "").strip().lower().startswith("test")]
        except Exception:
            return []
    return _TEST_IDS


def _home_branches(db, user: models.User) -> set:
    """Xodimning O'Z ish joyi: asosiy filial."""
    out = set()
    if getattr(user, "branch_id", None):
        out.add(user.branch_id)
    return out


def hidden_branch_ids(db, user: models.User) -> list:
    """Xodimga TANLAGICHDA ko'rinmasligi kerak bo'lgan filiallar.

    2026-08-27, Jahongir: "marhaboga test filial, Stech korsatmasin
    Stech umuman alohida markaz".

    QOIDA:
      - ASOSCHI hammasini ko'radi;
      - o'sha filial xodimning ASOSIY ish joyi bo'lsa — ko'rinadi
        (Stech'da ishlaydigan Husayn Stech'ni ko'rishi kerak);
      - qolganlarga hamkor markaz (Stech) va test filiali
        ko'rsatilmaydi.

    ASOSIY ish joyi bo'yicha tekshiriladi, "biriktirilgan filiallar"
    bo'yicha emas. Sabab: xodim mashq uchun test filialiga
    vaqtinchalik biriktirilgan bo'lishi mumkin — bu uning kundalik
    hisobotiga soxta raqam qo'shishi kerak emas.

    ISTISNO — HR RAHBARI (2026-08-31, Jahongir: "test filial HR
    rahbariga ko'rinsin, u ishlatib ko'radi tekshiradi"). HR
    xodimlarni o'rgatadi va yangi bo'limlarni sinab ko'radi —
    mashq filiali unga ish quroli.

    Hamkor markaz (Stech) esa unga BARIBIR yopiq: u boshqa
    biznesning puli, o'rganishga aloqasi yo'q.

    DIQQAT — YIG'INDIGA TA'SIR QILMAYDI. Bu ro'yxat faqat
    TANLAGICH uchun. Test filialining soxta raqamlari "barcha
    filiallar" yig'indisiga baribir qo'shilmaydi — u alohida
    ro'yxat (aggregate_skip_ids) bilan boshqariladi va u
    o'zgarmadi. Ya'ni HR test filialini ochib ko'ra oladi,
    lekin uning raqami hech kimning hisobotini buzmaydi.
    """
    if getattr(user, "role", None) == roles.FOUNDER:
        return []
    hide = set(partner_branch_ids(db))
    if getattr(user, "role", None) not in roles.TEST_BRANCH_VIEW:
        hide |= set(test_branch_ids(db))
    return sorted(hide - _home_branches(db, user))


def aggregate_skip_ids(db, user: models.User) -> list:
    """"Barcha filiallar" YIG'INDISIGA qo'shilmaydigan filiallar.

    Bu ro'yxat HAMMAGA, shu jumladan ASOSCHIGA ham tegishli:
      - hamkor markaz (Stech) — 2026-08-15, Jahongir: "uni men
        umuman boshqarmayman, faqat asoschi sifatida 40% ulushim
        bor". Uning aylanmasi Jony Academy yig'indisiga
        qo'shilmasligi kerak;
      - test filiali — 2026-08-27: unda soxta o'quvchi va soxta lid
        bor, ular real ko'rsatkichni buzadi.

    Xodimning O'Z ish joyi bundan mustasno: Stech'da ishlaydigan
    odam "barcha filiallar" rejimida o'z o'quvchilarini ko'rishi
    kerak.
    """
    skip = set(partner_branch_ids(db)) | set(test_branch_ids(db))
    return sorted(skip - _home_branches(db, user))


def blocked_branch_ids(db, user: models.User) -> list:
    """Server QAT'IY yopadigan filiallar (tanlab ham ochilmaydi).

    Faqat HAMKOR markaz — u boshqa biznesning ma'lumoti.

    Test filiali bu ro'yxatga KIRMAYDI: interaktiv o'rgatuvchi
    (guide.py) mashq paytida global filialni ataylab test filialiga
    o'tkazadi. Uni qat'iy yopsak, o'rgatuvchi bo'sh ekran
    ko'rsatardi. Test filiali tanlagichda ko'rinmaydi va UMUMIY
    yig'indiga qo'shilmaydi — shuning o'zi yetarli.
    """
    if getattr(user, "role", None) == roles.FOUNDER:
        return []
    return sorted(set(partner_branch_ids(db)) - _home_branches(db, user))


def visible_branch_ids(db, user: models.User) -> list:
    """Xodim tanlay oladigan filiallar (tanlagich ro'yxati uchun)."""
    hide = set(hidden_branch_ids(db, user))
    return [b.id for b in db.query(models.Branch)
            .order_by(models.Branch.name).all() if b.id not in hide]


def reset_partner_cache():
    """Filial hamkorligi yoki nomi o'zgarganda chaqiriladi."""
    global _PARTNER_IDS
    _PARTNER_IDS = None
    global _TEST_IDS
    _TEST_IDS = None


def scope_to_branch(query, model, user: models.User, branch_id=None,
                    keep_unset: bool = False):
    """Filialga bo'yicha cheklash.

    Uch xil cheklash bor va ular aralashmasligi kerak:
      1) HUQUQ - filialga bog'langan xodim faqat O'Z FILIALLARINI
         (asosiy + qo'shimcha) ko'radi. Buni hech kim aylanib o'tolmaydi.
      2) FILTR - butun tashkilotni ko'radigan odam (asoschi, HR, SMM)
         istagan filialni alohida ko'rmoqchi bo'lsa, branch_id beradi.
      3) HAMKOR FILIAL (2026-08-15) - "barcha filiallar" rejimida
         hamkor markaz raqamlari CHIQARIB TASHLANADI. U alohida
         biznes; tanlab ko'rish mumkin, lekin umumiy yig'indiga
         qo'shilmaydi.

    keep_unset (2026-08-28) — FILIALSIZ yozuvlar ham ko'rinsinmi.

    Standart holat: YO'Q. Pulga tegadigan narsalarda (o'quvchi,
    to'lov, xarajat) filialsiz yozuv chiqib qolsa, bir filial
    boshqasining raqamini ko'rib qolardi.

    Lekin KONTENT boshqacha: post umuman markazniki, bitta
    filialniki emas. Aynan shu farq tufayli Jahongirning sentabr
    kontent-plani ko'rinmay qoldi — u Excelni yuklaganda qatorlar
    filialsiz saqlangan, tanlagichda esa "Bekobod 1" turgan edi va
    filialsiz qatorlar filtrdan o'tmagan. Ro'yxat bo'm-bo'sh
    ko'rindi, ma'lumot esa joyida edi.
    """
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = _user_branch_ids(query.session, user)
        # O'z filiallaridan bittasini tanlab ko'rishi mumkin
        if branch_id and branch_id in allowed:
            if keep_unset:
                return query.filter(or_(model.branch_id == branch_id,
                                        model.branch_id.is_(None)))
            return query.filter(model.branch_id == branch_id)
        if keep_unset:
            return query.filter(or_(model.branch_id.in_(allowed or [-1]),
                                    model.branch_id.is_(None)))
        return query.filter(model.branch_id.in_(allowed or [-1]))
    # 2026-08-27: yashirin filial (hamkor Stech, test) — tanlab ham
    # ko'rib bo'lmaydi. Avval faqat "barcha filiallar" rejimida
    # chiqarib tashlanardi, lekin tanlagichdan tanlansa ochilib
    # ketaverardi.
    if not hasattr(model, "branch_id"):
        return query
    if branch_id:
        # Hamkor markazni tanlab ham ochib bo'lmaydi
        if branch_id in blocked_branch_ids(query.session, user):
            return query.filter(model.branch_id == -1)
        if keep_unset:
            return query.filter(or_(model.branch_id == branch_id,
                                    model.branch_id.is_(None)))
        return query.filter(model.branch_id == branch_id)
    # "Barcha filiallar" — hamkor markaz ham, TEST filiali ham
    # yig'indiga qo'shilmaydi. Test filialida soxta o'quvchi va
    # soxta lid bor; ular real ko'rsatkichni buzadi (aynan shu
    # sabab marketologda 49 ta lid ko'rinardi).
    #
    # DIQQAT: bu yerda hidden_branch_ids EMAS, aggregate_skip_ids
    # ishlatiladi. Farqi: asoschi tanlagichda Stech'ni KO'RADI
    # (tanlab, alohida qaray oladi), lekin uning raqami umumiy
    # yig'indiga QO'SHILMAYDI. Ikkalasini bitta ro'yxat qilib
    # qo'ysam, asoschining umumiy tushumiga Stech puli qo'shilib
    # ketardi — test_courses_partner aynan shuni tutdi.
    skip = aggregate_skip_ids(query.session, user)
    if skip:
        return query.filter(or_(model.branch_id.is_(None),
                                model.branch_id.notin_(skip)))
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
        max_score=exam.max_score,
        # O'tish balli (2026-09-10): test yaratilganda muhrlangan
        # qiymat. Eski testlarda va Mock'da null.
        pass_percent=getattr(exam, "pass_percent", None),
        created_by=exam.created_by,
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
    if not lessons:
        return 0.0
    # 2026-08-15: ilgari HAR DARS uchun 3 ta alohida so'rov ketardi
    # (daraja tarixi + ustoz + yo'qlama soni). 360 dars = ~1000 so'rov.
    # Endi hammasi 3 ta so'rovda oldindan o'qiladi, hisob xotirada
    # bo'ladi. Natija AYNAN o'sha — mantiq o'zgarmagan.
    gi = billing.GradeIndex(db)
    counts = billing.attendance_counts(db, [l.id for l in lessons])
    total = 0.0
    _mc: dict = {}   # oy bo'luvchisi keshi (2026-08-19 qoidasi)
    for l in lessons:
        g = groups.get(l.group_id)
        if not g or l.teacher_id is None:
            continue
        per_student = gi.per_student(g, l.teacher_id, l.date)
        rate = billing.per_attendance_rate_m(db, g, l.date, per_student, _mc)
        total += counts.get(l.id, 0) * rate
    return round(total, 2)


# ---------------------------------------------------------------------
#  KO'P FILIALLI USTOZ OYLIGI (2026-09-15)
#
#  Jahongir: "Elena ustoz 2-3ta filialda ishlaydi lekin men bekobod 2
#  filialda avgust oyligini korsam yelena chiqmadi lekin dars otgan".
#
#  Sabab: oylik ro'yxatlari ustozni USTOZ KARTASIDAGI ASOSIY filial
#  (Teacher.branch_id) bo'yicha tanlardi. Asosiy filiali boshqa bo'lgan
#  ustoz tanlangan filialda dars o'tgan bo'lsa ham ro'yxatga kirmasdi;
#  "barcha filiallar"da esa butun oyligi asosiy filialiga yozilardi.
#  Foyda-zarar hisobi (_payroll_total) esa guruh filialidan yurardi —
#  ikki raqam bir-biriga mos kelmasdi.
#
#  Endi qoida bitta: oylik GURUH FILIALIGA tegishli. Filial tanlansa,
#  shu filial guruhlarida dars o'tgan har bir ustoz chiqadi va unga
#  faqat shu filial guruhlaridan hisoblangan summa ko'rsatiladi.
# ---------------------------------------------------------------------
def _payroll_branches(db: Session, user, branch_id=None):
    """Oylik qaysi filiallar bo'yicha ko'rsatiladi.

    None — cheklov yo'q (butun tashkilot, filial tanlanmagan).
    set — faqat shu filiallar guruhlari."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = set(_user_branch_ids(db, user))
        if branch_id and branch_id in allowed:
            return {branch_id}
        return allowed or {-1}
    if branch_id:
        if branch_id in blocked_branch_ids(db, user):
            return {-1}
        return {branch_id}
    return None


def _payroll_teacher_ids(db: Session, branches, start: date,
                         end: date) -> set:
    """Tanlangan filiallarga tegishli ustozlar: shu davrda shu filial
    guruhida dars o'tganlar + kartasida shu filial (asosiy yoki
    qo'shimcha) turganlar."""
    ids = set()
    gids = [g for (g,) in db.query(models.Group.id)
            .filter(models.Group.branch_id.in_(list(branches))).all()]
    for chunk in billing._chunks(gids):
        ids |= {t for (t,) in db.query(models.Lesson.teacher_id)
                .filter(models.Lesson.group_id.in_(chunk),
                        models.Lesson.held == 1,
                        models.Lesson.date >= start,
                        models.Lesson.date <= end,
                        models.Lesson.teacher_id.isnot(None))
                .distinct().all()}
    ids |= {t for (t,) in db.query(models.Teacher.id)
            .filter(models.Teacher.branch_id.in_(list(branches))).all()}
    ids |= {t for (t,) in db.query(models.TeacherBranch.teacher_id)
            .filter(models.TeacherBranch.branch_id.in_(list(branches))).all()}
    return ids


def _earned_in_branches(e: dict, groups: dict, branches) -> dict:
    """_teacher_earned() natijasidan faqat tanlangan filiallar
    guruhlarini qoldiradi. branches=None bo'lsa — o'zgarishsiz.
    "total_amount" — ustozning shu oydagi BARCHA filiallardagi summasi
    (to'lovni filialga ulush bo'yicha taqsimlash uchun)."""
    if branches is None:
        return dict(e, total_amount=e["amount"])
    keep = [g for g in e["by_group"]
            if getattr(groups.get(g.get("group_id")), "branch_id", None)
            in branches]
    return dict(e,
                by_group=keep,
                amount=round(sum(g["amount"] for g in keep), 2),
                attendances=sum(g["attendances"] for g in keep),
                lessons=sum(g["lessons"] for g in keep),
                total_amount=e["amount"])


def _paid_share(paid: float, part: float, whole: float) -> float:
    """Ustozga berilgan pul filiallarga ishlagan ulushi bo'yicha
    bo'linadi: bir odamning to'lovi ikki filial ro'yxatida ikki marta
    to'liq chiqib qolmasin."""
    if not whole or part >= whole:
        return round(paid, 2)
    return round(paid * part / whole, 2)


def _check_pay_scope(db: Session, user, teacher=None, staff_user=None) -> None:
    """Filialga bog'langan xodim (administrator, filial rahbari) faqat
    O'Z filiali ustozi yoki xodimiga pul beradi (2026-09-16, Jahongir:
    "administratorga oylik berish huquqini ber"). Qo'shimcha filial
    (teacher_branches / user_branches) ham hisobga olinadi."""
    if user.role in tuple(roles.ORG_WIDE_ROLES) or not user.branch_id:
        return
    allowed = set(_user_branch_ids(db, user))
    if teacher is not None:
        br = {teacher.branch_id} | {
            tb.branch_id for tb in db.query(models.TeacherBranch)
            .filter(models.TeacherBranch.teacher_id == teacher.id)}
        if not (br & allowed):
            raise HTTPException(403, "Bu ustoz boshqa filialga tegishli")
    if staff_user is not None:
        br = {staff_user.branch_id} | {
            ub.branch_id for ub in db.query(models.UserBranch)
            .filter(models.UserBranch.user_id == staff_user.id)}
        if not (br & allowed):
            raise HTTPException(403, "Bu xodim boshqa filialga tegishli")


def _pay_branch(db: Session, user, t, branch_id=None):
    """Ustozga berilgan pul QAYSI FILIALGA yoziladi (2026-09-16).

    1) Formada tanlangan filial (tepadagi filial yoki "Barcha
       filiallar"da qo'lda tanlangani);
    2) bo'lmasa — pulni kiritgan xodimning filiali;
    3) bo'lmasa — ustozning asosiy filiali.
    Filialga bog'langan xodim faqat o'z filiallaridan birini tanlay oladi."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = _user_branch_ids(db, user)
        if branch_id and int(branch_id) in allowed:
            return int(branch_id)
        return user.branch_id
    if branch_id:
        return int(branch_id)
    return t.branch_id


def _payroll_branch_label(t, group_branch_ids, names: dict, branches):
    """Oylik qatoridagi "Filial" yozuvi. Filial tanlanganda — dars
    o'tilgan guruh filiali; asosiy filiali boshqa bo'lsa qavsda."""
    home = names.get(t.branch_id)
    if branches is None:
        return home
    got = sorted({names.get(b) for b in group_branch_ids} - {None})
    if not got:
        return home
    label = ", ".join(got)
    if home and home not in got:
        label += f" (asosiy: {home})"
    return label


def _salary_breakdown(db: Session, t, year: int, month: int) -> dict:
    """USTOZ OYLIGI TO'LIQ: filial -> guruh -> o'quvchi (2026-09-15).

    Jahongir: "oqituvchilarga oyligini aynan qaysi oquvchi nechta kelgan
    toliq hisoboti oquvchilar kesimida guruhlar kesimida oziniki
    korinsin ... 2ta filialda ishlasa filiallar kesimida korinsin".

    Hisob _teacher_earned() bilan AYNAN bir xil qoidadan yuradi:
      - har belgi (keldi ham, kelmadi ham) = 1 yo'qlama x dars kunidagi
        narx (billing.per_attendance_rate_m);
      - guruhdan chiqqan o'quvchining oxirgi kelgan kunidan KEYINGI
        belgilari sanalmaydi (billing.attendance_cutoff_many) — ular
        "not_counted" bo'lib ko'rsatiladi, yashirilmaydi."""
    start, end = billing.month_bounds(year, month)
    period = f"{year:04d}-{month:02d}"
    ctx = billing.PayrollContext(db)
    ctx.prefetch([t.id])
    lessons = [l for l in ctx.lessons(t.id, start, end)
               if ctx.groups.get(l.group_id)]
    ctx.prefill_divisors(lessons)
    by_id = {l.id: l for l in lessons}

    marks = []                                  # (dars, o'quvchi, belgi)
    for chunk in billing._chunks(list(by_id)):
        for lid, sid, pr in (db.query(models.Attendance.lesson_id,
                                      models.Attendance.student_id,
                                      models.Attendance.present)
                             .filter(models.Attendance.lesson_id.in_(chunk))
                             .all()):
            marks.append((by_id[lid], sid, pr))
    per_group: dict = {}
    for les, sid, _pr in marks:
        per_group.setdefault(les.group_id, set()).add(sid)
    cut = billing.attendance_cutoff_many(db, per_group) if per_group else {}

    students: dict = {}
    for chunk in billing._chunks(sorted({sid for _l, sid, _p in marks})):
        for s in (db.query(models.Student.id, models.Student.full_name,
                           models.Student.status)
                  .filter(models.Student.id.in_(chunk)).all()):
            students[s.id] = s
    names = {b.id: b.name for b in db.query(models.Branch).all()}

    rates: dict = {}

    def rate_of(les):
        if les.id not in rates:
            g = ctx.groups[les.group_id]
            ps = ctx.grades.per_student(g, les.teacher_id, les.date)
            rates[les.id] = (billing.per_attendance_rate_m(
                db, g, les.date, ps, ctx.mcache), ps)
        return rates[les.id]

    branches: dict = {}

    def group_box(g):
        br = branches.setdefault(g.branch_id, {
            "branch_id": g.branch_id,
            "branch": names.get(g.branch_id) or "Filialsiz",
            "amount": 0.0, "attendances": 0, "lessons": 0,
            "not_counted": 0, "groups": {}})
        return br, br["groups"].setdefault(g.id, {
            "group_id": g.id, "group": g.name, "rate": 0.0,
            "rate_per_student_month": 0.0,
            "standard_lessons": g.standard_lessons_per_month or 12,
            "lessons": 0, "attendances": 0, "not_counted": 0,
            "amount": 0.0, "students": {}})

    for les in lessons:
        g = ctx.groups[les.group_id]
        br, gr = group_box(g)
        gr["lessons"] += 1
        br["lessons"] += 1
        gr["rate"], gr["rate_per_student_month"] = rate_of(les)

    for les, sid, pr in marks:
        g = ctx.groups[les.group_id]
        br, gr = group_box(g)
        rate, _ps = rate_of(les)
        st = students.get(sid)
        row = gr["students"].setdefault(sid, {
            "student_id": sid,
            "student": st.full_name if st else f"#{sid}",
            "status": st.status if st else None,
            "present": 0, "absent": 0, "counted": 0, "not_counted": 0,
            "amount": 0.0})
        if pr in (1, 2):
            row["present"] += 1
        else:
            row["absent"] += 1
        stop = cut.get(les.group_id, {}).get(sid)
        if stop is not None and les.date and les.date > stop:
            row["not_counted"] += 1
            gr["not_counted"] += 1
            br["not_counted"] += 1
            continue
        row["counted"] += 1
        row["amount"] += rate
        gr["attendances"] += 1
        gr["amount"] += rate
        br["attendances"] += 1
        br["amount"] += rate

    flat: dict = {}
    out_branches = []
    for br in sorted(branches.values(), key=lambda b: -b["amount"]):
        groups_out = []
        for gr in sorted(br["groups"].values(), key=lambda x: -x["amount"]):
            st_rows = sorted(gr["students"].values(),
                             key=lambda x: (-x["amount"], x["student"]))
            for r in st_rows:
                r["amount"] = round(r["amount"], 2)
                f = flat.setdefault(r["student_id"], {
                    "student_id": r["student_id"], "student": r["student"],
                    "status": r["status"], "present": 0, "absent": 0,
                    "counted": 0, "not_counted": 0, "amount": 0.0,
                    "groups": [], "branches": []})
                for k in ("present", "absent", "counted", "not_counted",
                          "amount"):
                    f[k] += r[k]
                if gr["group"] not in f["groups"]:
                    f["groups"].append(gr["group"])
                if br["branch"] not in f["branches"]:
                    f["branches"].append(br["branch"])
            groups_out.append(dict(gr, amount=round(gr["amount"], 2),
                                   students=st_rows))
        out_branches.append(dict(br, amount=round(br["amount"], 2),
                                 groups=groups_out))
    flat_rows = sorted(
        (dict(f, amount=round(f["amount"], 2),
              groups=", ".join(f["groups"]),
              branches=", ".join(f["branches"])) for f in flat.values()),
        key=lambda x: (-x["amount"], x["student"]))

    seal = _seal_rows(db, period, [t.id]).get(t.id)
    amount = round(sum(b["amount"] for b in out_branches), 2)
    return {
        "teacher_id": t.id,
        "full_name": t.full_name,
        "period": period,
        "title": _month_title(period),
        "sealed": seal is not None,
        "sealed_amount": (round(float(seal.amount or 0), 2)
                          if seal is not None else None),
        "amount": amount,
        "attendances": sum(b["attendances"] for b in out_branches),
        "lessons": len(lessons),
        "not_counted": sum(b["not_counted"] for b in out_branches),
        "multi_branch": len(out_branches) > 1,
        "branches": out_branches,
        "students": flat_rows,
    }


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

def _recharge_on_leave(db: Session, s: models.Student, group,
                       on: date = None, user=None) -> dict | None:
    """GURUHDAN CHIQQANDA shu oyning hisobini to'g'rilaydi.

    2026-08-15, Jahongir: "guruhdan chiqqanda avtomat shu kungacha
    qatnashgan darslarini hisoblanib hisobi ham togrlanishi kerak".

    Oy boshida butun oy uchun pul yechilgan bo'ladi. O'quvchi oy
    o'rtasida chiqsa, u kelmagan darslar uchun to'lashi shart emas —
    shuning uchun hisob CHIQQAN KUNGACHA O'TILGAN darslar bo'yicha
    qayta hisoblanadi va farq balansga qaytadi.

    Faqat HAQIQATDA O'TILGAN darslar (held=1) sanaladi. Chegirma
    ham hisobga olinadi. Hisob qatori hali yozilmagan bo'lsa hech
    narsa qilinmaydi.
    """
    if group is None:
        return None
    on = on or roles.local_today()
    period = f"{on.year:04d}-{on.month:02d}"
    row = (db.query(models.Payment)
           .filter(models.Payment.student_id == s.id,
                   models.Payment.kind == "charge",
                   models.Payment.period == period)
           .order_by(models.Payment.id.desc()).first())
    if row is None:
        return None

    start, _end = billing.month_bounds(on.year, on.month)
    frm = start
    if s.enrolled_date and s.enrolled_date > start:
        frm = s.enrolled_date
    held = (db.query(models.Lesson)
            .filter(models.Lesson.group_id == group.id,
                    models.Lesson.held == 1,
                    models.Lesson.date >= frm,
                    models.Lesson.date <= on).count())
    cap = int(getattr(group, "standard_lessons_per_month", None) or 12)
    n = min(held, cap)
    try:
        disc = float(_student_discount_percent(db, s) or 0)
    except Exception:
        disc = 0.0
    unit = billing.student_lesson_price(s, group) * (100.0 - disc) / 100.0
    target = roles.money(n * unit)
    was = abs(float(row.amount or 0))
    if abs(was - target) < 1:
        return None

    row.amount = -abs(target)
    row.updated_at = datetime.utcnow()
    row.note = (f"{period} — guruhdan chiqdi ({on.isoformat()}): "
                f"{n} dars hisoblandi"
                + (f", chegirma {disc:.0f}%" if disc else ""))
    try:
        audit.log(db, user, entity="payment", action="amount_edit",
                  entity_id=row.id, entity_label=s.full_name,
                  field="amount",
                  old_value=f"{was:,.0f}".replace(",", " "),
                  new_value=f"{target:,.0f}".replace(",", " "),
                  note=(f"Guruhdan chiqarildi — {n} ta o'tilgan dars "
                        "bo'yicha qayta hisoblandi"),
                  branch_id=s.branch_id)
    except Exception:
        pass
    return {"lessons": n, "was": was, "now": target,
            "returned": round(was - target)}


def _recharge_after_move(db: Session, s: models.Student,
                         old_group, new_group, on_date: date = None,
                         user=None) -> dict | None:
    """Oy o'rtasida guruh almashsa — shu oyning hisobini QAYTA bo'ladi.

    2026-08-13, Jahongir: narxi boshqa guruhga o'tganda o'sha oyning
    hisobi eski narxda qolib ketardi. Endi muzlatishdagi kabi:
    ko'chgan kungacha bo'lgan darslar ESKI guruh narxida, o'sha kundan
    oy oxirigacha YANGI guruh narxida hisoblanadi va oyning yagona
    hisob qatori shunga qarab to'g'rilanadi. Eski summa audit
    jurnalida qoladi.

    Hisob qatori hali yozilmagan bo'lsa — hech narsa qilinmaydi:
    oylik hisob-kitob keyin yurgizilganda baribir yangi guruh
    narxida hisoblanadi.
    """
    on = on_date or roles.local_today()
    period = f"{on.year:04d}-{on.month:02d}"
    row = (db.query(models.Payment)
           .filter(models.Payment.student_id == s.id,
                   models.Payment.kind == "charge",
                   models.Payment.period == period)
           .order_by(models.Payment.id.desc()).first())
    if row is None:
        return None

    start, end = billing.month_bounds(on.year, on.month)
    try:
        disc = float(_student_discount_percent(db, s) or 0)
    except Exception:
        disc = 0.0
    k = (100.0 - disc) / 100.0

    def _unit(g):
        return float((getattr(g, "lesson_price", 0) or 0)) * k

    def _std(g):
        return int(getattr(g, "standard_lessons_per_month", None) or 12)

    def _count(g, frm, to):
        if not g or frm > to:
            return 0
        return (db.query(models.Lesson)
                .filter(models.Lesson.group_id == g.id,
                        models.Lesson.date >= frm,
                        models.Lesson.date <= to).count())

    old_n = min(_count(old_group, start, on - timedelta(days=1)),
                _std(old_group) if old_group else 0)
    new_n = min(_count(new_group, on, end), _std(new_group))
    target = roles.money(old_n * _unit(old_group) + new_n * _unit(new_group))
    was = abs(float(row.amount or 0))
    if abs(was - target) < 1:
        return None

    # IZOH: qaysi guruh uchun qancha pul hisoblangani ochiq yozilsin
    # (Jahongir, 2026-08-13: "qaysi guruh uchun qancha pul
    # hisoblanganligi korinib tursa boldi").
    o_name = getattr(old_group, "name", "—")
    n_name = getattr(new_group, "name", "—")

    def _som(v):
        return f"{v:,.0f}".replace(",", " ")

    parts = []
    if old_n:
        parts.append(f"{o_name}: {old_n} dars x {_som(_unit(old_group))} "
                     f"= {_som(old_n * _unit(old_group))}")
    if new_n:
        parts.append(f"{n_name}: {new_n} dars x {_som(_unit(new_group))} "
                     f"= {_som(new_n * _unit(new_group))}")
    row.amount = -target
    row.note = (f"{period} — guruh almashdi · " + " + ".join(parts)
                + f" [dars:{old_n + new_n}]")
    audit.log(db, user, entity="payment", action="lessons_recount",
              entity_id=row.id, entity_label=s.full_name, field="amount",
              old_value=f"{was:,.0f}".replace(",", " "),
              new_value=f"{target:,.0f}".replace(",", " "),
              note=f"Guruh almashdi: {o_name} → {n_name}",
              branch_id=s.branch_id)
    return {"old": was, "new": target, "old_lessons": old_n,
            "new_lessons": new_n}


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

def _close_request_tasks(db: Session, title_prefix: str,
                         result: str) -> int:
    """SO'ROV HAL BO'LDI — unga bog'liq BARCHA vazifalar yopiladi.

    2026-08-20, Jahongir: "vazifalardan tasdiqlansan vazifa avtomat
    bajarilgan bo'lsin ... boshqa sorovlar ham tasdiqlansa vazifada
    ham bajarildi bo'lsin".

    So'rov bir nechta tasdiqlovchiga alohida vazifa bo'lib tushadi.
    Bittasi hal qilgach qolganlarining ro'yxatida ochiq turib
    qolmasin - hammasi bir yo'la "bajarildi" bo'ladi. Vazifalar
    O'CHIRILMAYDI, natija yozilib yopiladi (tarix qoladi)."""
    rows = (db.query(models.Task)
            .filter(models.Task.title.like(title_prefix + "%"),
                    ~models.Task.status.in_(tuple(roles.TASK_CLOSED)))
            .all())
    for t in rows:
        t.status = "done"
        t.done_at = datetime.utcnow()
        t.result = result
    return len(rows)


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


def _notify_reschedule_approvers(db: Session, r, group, teacher) -> None:
    """Dars ko'chirish so'rovi HAR BIR tasdiqlovchiga vazifa bo'lib tushadi.

    2026-08-24, Jahongir: "HR uchun dars tasdiqlash chiqmay qolibdi
    dars kochirishlarniki".

    SABAB. Ilgari bu yerda _hr_task() ishlatilardi — u so'rovni FAQAT
    BITTA odamga biriktirardi (ro'yxatdagi birinchi topilganga, ya'ni
    amalda asoschiga). Natijada HR va o'quv bo'limi rahbari so'rovni
    umuman ko'rmasdi. Chegirma so'rovida bu allaqachon to'g'ri
    ishlangan (_notify_discount_approvers) — dars ko'chirish ham
    o'shanday bo'ldi.

    Kim ko'radi: asoschi, o'quv bo'limi rahbari va HR — butun
    tashkilot bo'yicha; filial rahbari — faqat o'z filialining
    guruhlari bo'yicha.

    Bittasi hal qilgach _close_request_tasks() qolganlarining
    vazifasini ham "bajarildi" qilib yopadi.
    """
    title = f"Dars ko'chirish so'rovi #{r.id}"
    body = (f"{teacher.full_name if teacher else '—'} — "
            f"{group.name if group else '—'}\n"
            f"{r.from_date} → {r.to_date}\n"
            f"Sabab: {roles.RESCHEDULE_REASON_LABELS.get(r.reason or '', '—')}"
            f"\nIzoh: {r.note or '—'}\n"
            f"Kvota tugagan (oyiga {roles.RESCHEDULE_PER_MONTH} marta), "
            f"shuning uchun tasdiq kerak.\n"
            "Tasdiqlash: shu vazifaning ichidagi tugmadan yoki bosh "
            "sahifadagi \"Dars ko'chirish so'rovlari\" blokidan.")
    bid = group.branch_id if group is not None else None
    seen = set()
    for role in roles.RESCHEDULE_APPROVE:
        q = db.query(models.User).filter(models.User.role == role,
                                         models.User.is_active == 1)
        if role == roles.BRANCH_MANAGER and bid:
            q = q.filter(models.User.branch_id == bid)
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
                branch_id=bid,
                deadline=date.today() + timedelta(days=1),
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

# Chegirma to'xtaydigan holatlar. "trial" bu ro'yxatda YO'Q — sinovdagi
# o'quvchi ham darsga qatnayapti, chegirmasi ishlashi kerak.
_DISCOUNT_STOP_STATUSES = ("frozen", "archived", "left")


def _expire_discounts(db: Session) -> int:
    """AVTOMAT: chegirma o'z-o'zidan to'xtaydigan holatlar.

    2026-08-22, Jahongir: "chegirma qoyilganda, oila qilib boglaganda
    xodim qilib boglaganda, bu xodim ishda[n] boshasa yoki o'quvchi
    faol bolmasa muzlatilgan arxivda bolsa chegirma avtomat bekor
    bolishi kerak".

    Qoidalar:
      1) muddati o'tgan            -> "Muddati tugagan";
      2) xodim ishdan ketgan       -> "Bekor qilingan" (xodim farzandi);
      3) o'quvchi MUZLATILGAN      -> "Vaqtincha to'xtatilgan" — u
         qaytib faollashsa chegirma O'ZI tiklanadi (muzlatish vaqtinchalik,
         shuning uchun butunlay bekor qilinmaydi);
      4) o'quvchi ARXIVDA/KETGAN   -> "Bekor qilingan".

    Oila chegirmasi bunga muhtoj emas: u FAOL farzandlar sonidan
    jonli hisoblanadi (_family_discount_percent) — biri muzlatilsa
    foiz o'zi tushadi.

    Hech kim qo'lda olib tashlashi shart emas; hamma o'zgarish
    cancelled_reason'da yozilib qoladi."""
    today = date.today()
    n = 0
    rows = (db.query(models.Discount)
            .filter(models.Discount.status.in_(("active", "paused"))).all())
    if not rows:
        return 0

    sids = {d.student_id for d in rows if d.student_id}
    smap = {}
    if sids:
        smap = {s.id: s for s in db.query(models.Student)
                .filter(models.Student.id.in_(sids)).all()}
    # Xodimlar bir so'rovda
    uids = {d.staff_user_id for d in rows if d.staff_user_id}
    umap = {}
    if uids:
        umap = {u.id: u for u in db.query(models.User)
                .filter(models.User.id.in_(uids)).all()}

    for d in rows:
        st = smap.get(d.student_id)
        stat = st.status if st else None

        # 3-4) O'quvchi faol emas — chegirma ishlamasligi kerak.
        # DIQQAT: "trial" (sinov darsida) ham O'QIYAPTI — unga tegilmaydi,
        # faqat muzlatilgan / arxiv / chiqib ketgan holatlar hisobga olinadi.
        if stat in _DISCOUNT_STOP_STATUSES:
            if stat == "frozen":
                if d.status != "paused":
                    d.status = "paused"
                    d.cancelled_reason = ("O'quvchi muzlatilgan — chegirma "
                                          "vaqtincha to'xtadi (faollashsa "
                                          "o'zi tiklanadi)")
                    n += 1
            else:                       # archived | left | boshqa
                d.status = "cancelled"
                d.cancelled_reason = (
                    f"O'quvchi {roles.STUDENT_STATUS_LABELS.get(stat, stat)} "
                    "— chegirma avtomat bekor qilindi")
                n += 1
            continue

        # Muzlatilgandan qaytdi — to'xtatilgani o'zi tiklanadi
        if d.status == "paused":
            if d.end_date and d.end_date < today:
                d.status = "expired"
                n += 1
                continue
            d.status = "active"
            d.cancelled_reason = None
            n += 1
            continue

        if d.end_date and d.end_date < today:
            d.status = "expired"
            n += 1
            continue

        # 2) Xodim ishdan ketdi
        if d.kind == "staff_child" and d.staff_user_id:
            emp = umap.get(d.staff_user_id)
            if not emp or not emp.is_active:
                d.status = "cancelled"
                d.cancelled_reason = (
                    "Xodim ishdan ketdi — chegirma avtomat bekor qilindi")
                n += 1
    if n:
        db.commit()
    return n

def _student_discount_percent(db: Session, s: models.Student,
                              skip_kinds=()) -> float:
    """O'quvchining jami chegirma foizi: oilaviy (avtomat) + tasdiqlangan
    chegirmalar. Chegara MAX_TOTAL_DISCOUNT_PERCENT.

    skip_kinds — hisobga OLINMAYDIGAN turlar. Referal dvigateliga kerak
    (2026-08-28, Jahongir: "oilaviy chegirmasi bo'lsa o'sha to'laydigan
    summadan 10% foiz hisoblanib ketaveradi"): referal foizi
    "boshqa chegirmalardan keyingi" summadan olinadi, shuning uchun
    dvigatel o'z chegirmasini chiqarib tashlab hisoblashi kerak. Aks
    holda o'z-o'ziga bog'liq halqa hosil bo'lardi."""
    total = 0.0 if "family" in skip_kinds else _family_discount_percent(db, s)
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == s.id,
                    models.Discount.status == "active").all())
    fee = s.group.monthly_fee if s.group else 0.0
    for d in rows:
        if d.kind == "family" or d.kind in skip_kinds \
                or not _discount_alive(d):
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

    # Eski narx himoyasi: o'quvchida qulflangan narx bo'lsa o'sha
    price = billing.student_lesson_price(s, s.group)
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
        # REFERAL: bu yo'l orqali kelgan o'quvchida ham bog'lanish
        # saqlansin (o'quvchi avval qo'lda ochilib, keyin lid bilan
        # bog'langan bo'lishi mumkin).
        if getattr(lead, "referrer_student_id", None) \
                and not getattr(s, "referred_by_student_id", None):
            s.referred_by_student_id = lead.referrer_student_id

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

def _task_late(t: models.Task) -> bool:
    """Muddati o'tgan va hali yopilmaganmi."""
    return bool(t.deadline and t.deadline < date.today()
                and t.status not in roles.TASK_CLOSED)


def _task_status(t: models.Task) -> str:
    """Vazifaning HAQIQIY holati.

    2026-08-27 TUZATISH. Jahongir: "vazifalar bo'limida jarayondaga
    o'tkizsa jarayonga o'tmayabdi vazifa, tekshriildiga otkizsayam
    o'tmayabdi. qayta ishlashgayam otmayabdi, faqat bajarildiga
    ishlayabdi, bekor qilindi ishladi qolgani ishlamayabdi."

    Sabab shu funksiyada edi. U muddati o'tgan har qanday ochiq
    vazifani "late" deb QAYTARARDI va haqiqiy statusni butunlay
    bosib ketardi:
        Jarayonda    -> ekranda "Kechikdi"  -> Jarayonda tabida yo'q
        Tekshiruvda  -> ekranda "Kechikdi"  -> Tekshiruvda tabida yo'q
        Qayta ishlash-> ekranda "Kechikdi"  -> o'sha tabda yo'q
    Bajarildi va Bekor qilindi esa TASK_CLOSED ichida bo'lgani
    uchun bosilmasdi — shuning uchun "faqat o'sha ikkitasi
    ishlayapti" deb ko'rinardi. Aslida status BAZAGA yozilgan edi,
    ekran uni ko'rsatmasdi.

    Endi kechikish ALOHIDA belgi (overdue/late), status esa o'zi
    bo'lib qoladi. Qizil "Kechikdi" chipi baribir ko'rinadi.
    """
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
        "overdue": _task_late(t),
        "priority": t.priority,
        "priority_label": roles.TASK_PRIORITY_LABELS.get(t.priority, t.priority),
        "priority_rank": roles.TASK_PRIORITY_RANK.get(t.priority, 2),
        "status": st,
        "status_label": roles.TASK_STATUS_LABELS.get(st, st),
        "status_tone": roles.TASK_STATUS_TONE.get(st, "slate"),
        "stored_status": t.status,
        # "late" endi status emas, BELGI. Ekran uni alohida qizil
        # chip qilib ko'rsatadi va "Kechikdi" filtri shunga qaraydi.
        "late": _task_late(t),
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
                    since: date = None, until: date = None,
                    ctx: "billing.PayrollContext | None" = None) -> dict:
    """Ustozning berilgan davrda ishlab topgan puli.

    until berilmasa — BUGUNGACHA. Ya'ni ustoz oy o'rtasida kirsa,
    "shu kungacha ishlab topganim" ni ko'radi.

    2026-09-05 (Jahongir: "shunaqa yuklashlar juda sekin bolyabdi"):
    dars boshiga 6-8 ta so'rov o'rniga hamma narsa to'plam bo'lib
    o'qiladi (billing.PayrollContext). Natija _teacher_earned_legacy()
    bilan AYNAN bir xil — test_payroll_speed.py isbotlaydi. Bir nechta
    ustoz/davr uchun chaqirilganda bitta ctx ni bo'lishib ishlatish
    yana tezroq."""
    until = until or date.today()
    if ctx is None:
        ctx = billing.PayrollContext(db)
    lessons = ctx.lessons(teacher_id, since, until)
    counts = ctx.count_for(lessons)
    ctx.prefill_divisors(lessons)

    total = 0.0
    attendances = 0
    by_group: dict[int, dict] = {}
    by_period: dict[str, dict] = {}

    for l in lessons:
        g = ctx.groups.get(l.group_id)
        if not g:
            continue
        # Stavka dars SANASIGA qarab olinadi: ustoz keyin ko'tarilgan
        # bo'lsa ham o'tgan oyning darslari eski narxda qoladi.
        per_student = ctx.grades.per_student(g, l.teacher_id, l.date)
        rate = billing.per_attendance_rate_m(db, g, l.date, per_student,
                                             ctx.mcache)
        n = counts.get(l.id, 0)
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


def _teacher_earned_legacy(db: Session, teacher_id: int, *,
                    since: date = None, until: date = None) -> dict:
    """ESKI (dars boshiga so'rov) yo'l — faqat test_payroll_speed.py
    yangi yo'l bilan solishtirish uchun saqlangan. Ishlab chiqarishda
    _teacher_earned() ishlaydi.

    Ustozning berilgan davrda ishlab topgan puli.

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

    _mc: dict = {}   # oy bo'luvchisi keshi (2026-08-19 qoidasi)
    for l in lessons:
        g = groups.get(l.group_id)
        if not g:
            continue
        # Stavka dars SANASIGA qarab olinadi: ustoz keyin ko'tarilgan
        # bo'lsa ham o'tgan oyning darslari eski narxda qoladi.
        rate, per_student = billing.lesson_rate(db, g, l, rates, _mc)
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
         .filter(models.Exam.group_id.in_(gids), models.Exam.date >= since,
                 models.Exam.kind != "kahoot"))   # o'yin — KPI emas
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
                  since: date = None, until: date = None,
                  ctx: "billing.PayrollContext | None" = None) -> float:
    rows = ctx.payments(teacher_id) if ctx is not None else None
    if rows is not None:
        # prefetch() qilingan — xotiradan, so'rovsiz. Shart SQL bilan
        # bir xil: paid_on bo'sh bo'lsa sana filtri uni tashlab ketadi.
        tot = 0.0
        for p in rows:
            if since and (p.paid_on is None or p.paid_on < since):
                continue
            if until and (p.paid_on is None or p.paid_on > until):
                continue
            tot += p.amount or 0
        return round(tot, 2)
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

_UZ_MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
              "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]


def _month_title(period: str) -> str:
    """"2026-08" -> "Avgust 2026"."""
    try:
        y, m = int(period[:4]), int(period[5:7])
        return f"{_UZ_MONTHS[m - 1]} {y}"
    except Exception:
        return period


def _month_name(period: str) -> str:
    """"2026-08" -> "Avgust"."""
    try:
        return _UZ_MONTHS[int(period[5:7]) - 1]
    except Exception:
        return period


def _pay_out(p: models.TeacherPayment) -> dict:
    return {
        "id": p.id, "amount": p.amount, "kind": p.kind,
        "kind_label": roles.TEACHER_PAYMENT_LABELS.get(p.kind, p.kind),
        "date": p.paid_on.isoformat() if p.paid_on else None,
        "period": p.period, "note": p.note, "by": p.created_by,
    }


# =====================================================================
#  OYLIK MUHRI (2026-09-07)
#
#  Jahongir: "taklifing menga maqul otgan oy muhransin".
#
#  Muammo: oylik hech qayerda saqlanmasdi — har safar yo'qlamadan
#  qayta hisoblanardi, shuning uchun oy yopilgandan keyingi har qanday
#  o'zgarish o'tgan oyning raqamini ham o'zgartirardi (31-avgustdagi
#  skrinshot bilan bugungi raqam mos kelmay qolgan edi).
#
#  Endi: oy tugagach raqam BIR MARTA muhrlanadi (PayrollSeal) va
#  keyin o'zgarmaydi. Muhr HECH QACHON o'chirilmaydi — asoschi
#  ataylab "qayta hisobla" desagina yangilanadi, eski qiymati esa
#  auditda qoladi.
# =====================================================================
def _period_closed(period: str) -> bool:
    """"YYYY-MM" tugab bo'lgan oymi?"""
    try:
        y, m = int(period[:4]), int(period[5:7])
    except Exception:
        return False
    t = roles.local_today()
    return (y, m) < (t.year, t.month)


def _seal_rows(db: Session, period: str, teacher_ids=None) -> dict:
    """{teacher_id: PayrollSeal} — shu oyning muhrlari."""
    q = db.query(models.PayrollSeal).filter(
        models.PayrollSeal.period == period)
    if teacher_ids:
        ids = [int(i) for i in teacher_ids]
        if not ids:
            return {}
        q = q.filter(models.PayrollSeal.teacher_id.in_(ids))
    try:
        return {r.teacher_id: r for r in q.all()}
    except Exception:
        db.rollback()
        return {}


def _seal_month(db: Session, year: int, month: int, *, by: str = "avtomat",
                force: bool = False, user=None) -> dict:
    """Shu oyni muhrlaydi. Idempotent: muhri bor ustozga tegilmaydi
    (force=True bo'lsa qayta hisoblab, eski qiymatni auditga yozadi).

    Faqat TUGAB BO'LGAN oy muhrlanadi — joriy oy hali davom etyapti."""
    period = f"{year:04d}-{month:02d}"
    out = {"period": period, "sealed": 0, "updated": 0, "skipped": 0}
    if not _period_closed(period):
        out["skipped"] = -1          # joriy/kelasi oy — muhrlanmaydi
        return out
    start, end = billing.month_bounds(year, month)
    teachers = db.query(models.Teacher).all()
    have = _seal_rows(db, period)
    if not force:
        teachers = [t for t in teachers if t.id not in have]
    if not teachers:
        return out
    ctx = billing.PayrollContext(db)
    ctx.prefetch([t.id for t in teachers])
    for t in teachers:
        try:
            e = _teacher_earned(db, t.id, since=start, until=end, ctx=ctx)
            if not e["lessons"] and not e["amount"]:
                continue
            old = have.get(t.id)
            payload = json.dumps(e["by_group"], ensure_ascii=False)
            if old is None:
                db.add(models.PayrollSeal(
                    period=period, teacher_id=t.id, branch_id=t.branch_id,
                    amount=e["amount"], attendances=e["attendances"],
                    lessons=e["lessons"], groups_json=payload,
                    sealed_by=by, revision=1))
                out["sealed"] += 1
            elif round(old.amount or 0, 2) != round(e["amount"], 2):
                audit.log(db, user, entity="teacher", action="update",
                          entity_id=t.id, entity_label=t.full_name,
                          field=f"oylik muhri {period}",
                          old_value=old.amount, new_value=e["amount"],
                          note="Muhr qayta hisoblandi", commit=False)
                old.amount = e["amount"]
                old.attendances = e["attendances"]
                old.lessons = e["lessons"]
                old.groups_json = payload
                old.sealed_at = datetime.utcnow()
                old.sealed_by = by
                old.revision = (old.revision or 1) + 1
                out["updated"] += 1
            db.commit()
        except Exception:
            db.rollback()
    return out


def _seal_closed_months(db: Session, back: int = 6) -> dict:
    """Muhrlanmagan tugagan oylarni muhrlaydi (kunlik cron uchun)."""
    t = roles.local_today()
    y, m = t.year, t.month
    res = {"months": []}
    for _ in range(max(1, back)):
        m -= 1
        if m < 1:
            y, m = y - 1, 12
        r = _seal_month(db, y, m)
        if r.get("sealed"):
            res["months"].append(r)
    return res


def _month_ledger(db: Session, t: models.Teacher) -> dict:
    """USTOZ OYLIGINING OYLAR BO'YICHA DAFTARI — bitta manba.

    Karta ("Darslarim va oyligim"), dashboard kartalari va Moliya
    bo'limi shu yerdan oladi, shuning uchun raqamlar hamma joyda bir xil.

    2026-09-05, Jahongir: "balans bilan o'tgan oyniki va bu oyniki ham
    turishi kerakda chunki otgan oy hali berilmasdan yangi oy
    boshlanganda ikkalasi qoshilsa balansda ustozlar bir oyniki deb
    oylab qolyabdi".

    NAVBAT QOIDASI (FIFO). Berilgan pul HAR DOIM ENG ESKI berilmagan
    oyning oyligiga yoziladi: avgust oyligi 5-sentabrda berilsa, u
    AVGUSTNIKI hisoblanadi (sentabrniki emas). Shunda:
      - "O'tgan oy qoldig'i" — o'tgan oy oyligining hali berilmagan qismi;
      - "Bu oy qoldig'i"     — shu oyda ishlab topilganning berilmagan qismi;
      - "Balans"             — ikkalasining (va undan oldingilarning) yig'indisi.
    Umumiy balans (ishlab topgan - olgan) bu qoidadan o'zgarmaydi — faqat
    qaysi oyga tegishli ekani aniq bo'ladi. Hamma oylar yopilib ortiqcha
    berilgan bo'lsa, ortiqcha to'lov o'z oyiga manfiy qoldiq bo'lib yoziladi.

    Hech narsa saqlanmaydi: har safar yo'qlamadan qayta hisoblanadi."""
    today = date.today()
    cur = today.isoformat()[:7]
    ctx = billing.PayrollContext(db)
    ctx.prefetch([t.id])
    all_time = _teacher_earned(db, t.id, ctx=ctx)

    pays = (db.query(models.TeacherPayment)
            .filter(models.TeacherPayment.teacher_id == t.id)
            .order_by(models.TeacherPayment.paid_on,
                      models.TeacherPayment.id).all())

    months = {p["period"] for p in all_time["by_period"]}
    months |= {p.paid_on.isoformat()[:7] for p in pays if p.paid_on}
    months.add(cur)
    first = min(months)
    fy, fm = int(first[:4]), int(first[5:7])
    seq = []
    y, m = fy, fm
    last = max(months)
    ly, lm = max((today.year, today.month), (int(last[:4]), int(last[5:7])))
    while (y, m) <= (ly, lm):
        seq.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1

    # MUHRLANGAN OYLAR (2026-09-07, Jahongir: "otgan oy muhransin").
    # Tugagan oyning raqami bir marta muhrlanadi va keyin o'zgarmaydi.
    seals: dict = {}
    try:
        for r in (db.query(models.PayrollSeal)
                  .filter(models.PayrollSeal.teacher_id == t.id).all()):
            seals[r.period] = r
    except Exception:
        db.rollback()

    rows: dict = {}
    for per in seq:
        y, m = int(per[:4]), int(per[5:7])
        ms, me = billing.month_bounds(y, m)
        e = _teacher_earned(db, t.id, since=ms, until=me, ctx=ctx)
        sl = seals.get(per)
        if sl is not None:
            try:
                e = {"amount": float(sl.amount or 0),
                     "attendances": int(sl.attendances or 0),
                     "lessons": int(sl.lessons or 0),
                     "by_group": json.loads(sl.groups_json or "[]")}
            except Exception:
                pass
        rows[per] = {
            "period": per,
            "title": _month_title(per),
            "is_current": per == cur,
            "sealed": sl is not None,
            "sealed_at": (sl.sealed_at.isoformat()
                          if sl is not None and sl.sealed_at else None),
            "lessons": e["lessons"],
            "attendances": e["attendances"],
            "earned": e["amount"],
            "by_group": e["by_group"],
            # shu oyda QO'LGA TEKKAN pul (sana bo'yicha) — ma'lumot uchun
            "paid_in_month": 0.0,
            "paid_advance": 0.0, "paid_salary": 0.0, "paid_correction": 0.0,
            # shu OY OYLIGI uchun berilgan (navbat qoidasi bilan)
            "paid_for": 0.0,
            "payments": [],       # shu oy oyligiga yozilgan to'lovlar
        }

    # --- navbat qoidasi: har to'lov eng eski berilmagan oyga ---------
    need = {per: float(rows[per]["earned"]) for per in seq}

    def _put(per, p, amount, split):
        rows[per]["paid_for"] += amount
        need[per] -= amount
        d = _pay_out(p)
        d["applied"] = round(amount, 2)
        d["split"] = split
        rows[per]["payments"].append(d)

    for p in pays:
        a = float(p.amount or 0)
        pm = p.paid_on.isoformat()[:7] if p.paid_on else cur
        home = pm if pm in rows else seq[-1]
        r0 = rows[home]
        r0["paid_in_month"] += a
        k = p.kind if p.kind in ("advance", "salary", "correction") \
            else "correction"
        r0[f"paid_{k}"] += a
        if a <= 0:
            # Manfiy tuzatish — o'z oyiga (qoldiq shuncha oshadi)
            _put(home, p, a, False)
            continue
        whole = a
        for per in seq:
            if need[per] <= 0.005:
                continue
            take = min(a, need[per])
            _put(per, p, take, abs(take - whole) > 0.005)
            a -= take
            if a <= 0.005:
                break
        if a > 0.005:
            # Hamma oylar yopilgan — ortiqcha berilgan, o'z oyiga
            _put(home, p, a, abs(a - whole) > 0.005)

    out = []
    for per in seq:
        r = rows[per]
        for k in ("paid_in_month", "paid_advance", "paid_salary",
                  "paid_correction", "paid_for"):
            r[k] = round(r[k], 2)
        r["left"] = round(r["earned"] - r["paid_for"], 2)
        out.append(r)

    total_paid = round(sum(p.amount or 0 for p in pays), 2)
    return {
        "months": out,                   # xronologik (eski -> yangi)
        "by_period_map": rows,
        "all_time": all_time,
        "pays": pays,
        "earned_total": all_time["amount"],
        "paid_total": total_paid,
        "balance": round(all_time["amount"] - total_paid, 2),
        "since": seq[0],
        "current": cur,
    }


def _balance_split(led: dict) -> dict:
    """Balansni "o'tgan oy / bu oy / undan oldingi" ga ajratadi."""
    months = led["months"]
    cur = led["current"]
    idx = [m["period"] for m in months].index(cur)
    this = months[idx]
    prev = months[idx - 1] if idx >= 1 else None
    older_left = round(sum(m["left"] for m in months[:max(0, idx - 1)]), 2)
    # Kelajak oylariga (oldindan berilgan) yozilganlar ham balansda
    future_left = round(sum(m["left"] for m in months[idx + 1:]), 2)
    month_left = this["left"]
    prev_left = prev["left"] if prev else 0.0
    parts = []
    if older_left:
        parts.append(f"oldingi oylar {older_left:,.0f}")
    if prev:
        parts.append(f"{_month_name(prev['period'])} {prev_left:,.0f}")
    parts.append(f"{_month_name(cur)} {month_left:,.0f}")
    if future_left:
        parts.append(f"oldindan {future_left:,.0f}")
    label = " + ".join(parts).replace(",", " ")
    return {
        "prev_period": prev["period"] if prev else None,
        "prev_title": prev["title"] if prev else None,
        "prev_earned": prev["earned"] if prev else 0.0,
        "prev_paid_for": prev["paid_for"] if prev else 0.0,
        "prev_left": prev_left,
        "month_paid_for": this["paid_for"],
        "month_left": month_left,
        "older_left": older_left,
        "future_left": future_left,
        "balance_label": label,
    }


def _salary_card(db: Session, t: models.Teacher) -> dict:
    """Ustozning ish haqi kartasi: ishlab topgan, olgan, balans.

    2026-09-05: balans yonida O'TGAN OY va BU OY qoldig'i alohida
    (navbat qoidasi — _month_ledger izohiga qarang)."""
    led = _month_ledger(db, t)
    cur = led["current"]
    this = led["by_period_map"][cur]
    split = _balance_split(led)
    balance = led["balance"]
    pays = list(reversed(led["pays"]))[:50]        # eng yangisi tepada

    # Eski maydon saqlanadi: bu oy boshigacha bo'lgan farq (sana bo'yicha)
    prev_months = [m for m in led["months"] if m["period"] < cur]
    carry = round(sum(m["earned"] for m in prev_months)
                  - sum(m["paid_in_month"] for m in prev_months), 2)

    return {
        "teacher_id": t.id,
        "full_name": t.full_name,
        "branch": t.branch.name if t.branch else None,
        # Shu oy
        "month": cur,
        "month_title": this["title"],
        "earned_month": this["earned"],
        "paid_month": this["paid_in_month"],
        "lessons_month": this["lessons"],
        "attendances_month": this["attendances"],
        # Umumiy balans
        "earned_total": led["earned_total"],
        "paid_total": led["paid_total"],
        "balance": balance,
        # BALANS AJRATMASI: o'tgan oy / bu oy (navbat qoidasi)
        **split,
        # O'tgan oylardan kelgan farq (sana bo'yicha) — eski maydon
        "carry": carry,
        "carry_label": (
            "O'tgan oylardan qarzimiz" if carry > 0
            else "O'tgan oyda ortiqcha berilgan" if carry < 0
            else "O'tgan oylar yopilgan"),
        # Avans chegarasi: ishlab topganidan ortiq berilmaydi
        "advance_available": max(0.0, balance),
        "by_group": this["by_group"],
        "by_period": led["all_time"]["by_period"][-12:],
        "payments": [_pay_out(p) for p in pays],
    }


def _finance_ledger(db: Session, t: models.Teacher) -> dict:
    """USTOZNING MOLIYA BO'LIMI — oylar bo'yicha oylik tarixi.

    2026-09-05, Jahongir: "ustozlarda moliya bo'limi qo'shilib oldin
    olgan oyliklari har oylik oyliklar o'sha yerga hisoblanib borsin
    oyliklar tarixi bo'lsin".

    Har oy: ISHLAB TOPGAN (o'sha oyning darslari, o'sha kundagi stavka),
    SHU OY OYLIGI UCHUN BERILGAN (navbat qoidasi — _month_ledger),
    QOLDIQ, va shu oy oyligiga yozilgan to'lovlar ro'yxati. Eng yangi
    oy tepada; bo'sh oylar ham ko'rinadi — tarix uzilmasin."""
    led = _month_ledger(db, t)
    split = _balance_split(led)
    return {
        "teacher_id": t.id,
        "full_name": t.full_name,
        "branch": t.branch.name if t.branch else None,
        "since": led["since"],
        "month": led["current"],
        "earned_total": led["earned_total"],
        "paid_total": led["paid_total"],
        "balance": led["balance"],
        **split,
        "months": [dict(m) for m in reversed(led["months"])],
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

def _my_teacher_cards(db: Session, user: models.User,
                      branch_id: int | None = None) -> list:
    t = _teacher_of_user(db, user)
    if not t:
        return []
    today = date.today()
    # Karta bilan bir xil manba (2026-09-05): balans yonida o'tgan oy /
    # bu oy qoldig'i alohida ko'rinadi — "bir oyniki" deb o'ylamasin.
    led = _month_ledger(db, t)
    this = led["by_period_map"][led["current"]]
    split = _balance_split(led)
    earned = {"amount": this["earned"], "lessons": this["lessons"],
              "attendances": this["attendances"]}
    paid = this["paid_in_month"]
    balance = led["balance"]

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
              split["balance_label"] if balance
              else "hisob yopilgan",
              "good" if balance > 0 else "bad" if balance < 0 else "plain",
              "/teachers"),
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

def _my_sales_cards(db: Session, user: models.User,
                    branch_id: int | None = None) -> list:
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())

    # 2026-08-27: bu yerda ham tanlagich e'tiborsiz qolgan edi.
    leads = scope_to_branch(
        db.query(models.Lead), models.Lead, user, branch_id
    ).filter(models.Lead.created_at >= d0).all()
    converted = [l for l in leads if l.stage == "converted"]

    # O'zi qabul qilgan pul
    pays = db.query(models.Payment).filter(
        models.Payment.kind == "payment",
        models.Payment.created_by == user.full_name,
        models.Payment.created_at >= d0).all()

    debt_q = scope_to_branch(db.query(models.Student), models.Student, user, branch_id)
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

def _my_hr_cards(db: Session, user: models.User,
                 branch_id: int | None = None) -> list:
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

def _my_academic_cards(db: Session, user: models.User,
                       branch_id: int | None = None) -> list:
    today = date.today()
    groups = scope_to_branch(db.query(models.Group), models.Group, user, branch_id).all()
    rooms = {r.id: r for r in db.query(models.Room).all()}
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()

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

def _my_exam_cards(db: Session, user: models.User,
                   branch_id: int | None = None) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    exams = db.query(models.Exam).filter(models.Exam.date >= m_start,
                                         models.Exam.kind != "kahoot").all()
    draft = [e for e in exams if (e.status or "done") == "draft"]
    done = [e for e in exams if e.status == "done"]
    return [
        _card("Shu oy imtihonlar", len(exams), None, "brand", "/audit"),
        _card("Tasdiq kutayotgan", len(draft), None,
              "bad" if draft else "good", "/audit"),
        _card("O'tkazilgan", len(done), None, "good", "/audit"),
    ]

def _my_facility_cards(db: Session, user: models.User,
                       branch_id: int | None = None) -> list:
    assets = scope_to_branch(db.query(models.Asset), models.Asset, user, branch_id).all()
    broken = [a for a in assets if a.condition in ("repair", "broken")]
    low = [c for c in scope_to_branch(
        db.query(models.Consumable), models.Consumable, user, branch_id).all()
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


def _my_marketing_cards(db: Session, user: models.User,
                        branch_id: int | None = None) -> list:
    today = date.today()
    m_start, _e = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(m_start, datetime.min.time())
    # 2026-08-27 TUZATISH. Jahongir: "Marhabo mamatqulova shu qizimiz
    # dashboardga kriganda 49ta lid korinyabdi, hamma filiallni
    # tanlasa, zafarni tanlasa ham shu chiqyabdi unga togri chiqarsin
    # filiallar boyicha ham".
    #
    # Sabab shu yerda edi: lidlar HECH QANDAY filial filtrisiz
    # sanalardi. Ya'ni raqamga test filialining soxta lidlari ham,
    # hamkor markaz (Stech) lidlari ham qo'shilib ketardi va
    # tepadagi tanlagich umuman ta'sir qilmasdi.
    #
    # Endi uchala raqam ham scope_to_branch orqali o'tadi: u rol
    # huquqini ham, tanlangan filialni ham, yashirin filiallarni ham
    # bir joyda hal qiladi.
    leads = scope_to_branch(
        db.query(models.Lead), models.Lead, user, branch_id
    ).filter(models.Lead.created_at >= d0).all()
    conv = [l for l in leads if l.stage == "converted"]
    spend = sum(e.amount for e in scope_to_branch(
        db.query(models.Expense), models.Expense, user, branch_id
    ).filter(models.Expense.category == "ads",
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
        # Reja/fakt ham TANLANGAN filial bo'yicha (avval doim
        # xodimning o'z filiali olinardi — shuning uchun
        # sarlavhada "Maktab", tanlagichda "Zafar" turardi).
        st8 = _smm_sales_state(db, branch_id or user.branch_id,
                               today.year, today.month)
        if st8["percent"] is None:
            # Joriy oyda reja yo'q - keyingi oydan boshlanayotgan
            # bo'lsa (masalan, sentabrdan) shuni ko'rsatamiz
            ny, nm = ((today.year + 1, 1) if today.month == 12
                      else (today.year, today.month + 1))
            nxt = _smm_sales_state(db, branch_id or user.branch_id, ny, nm)
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

    # IJTIMOIY TARMOQ OBUNACHILARI (2026-08-27).
    # Jahongir: "SMMda ijtimoiy tarmoqlardagi obunachilar soni ham
    # dashboardda korinib tursin."
    #
    # DIQQAT: bu yerda TARMOQQA CHIQILMAYDI. /api/social sahifasi
    # ochilganda obunachilar o'zi yangilanadi va bazaga yoziladi;
    # dashboard esa faqat OXIRGI yozuvni o'qiydi. Aks holda har bir
    # dashboard ochilishi Instagram/Telegram'ga so'rov yuborardi va
    # sahifa sekinlashardi.
    try:
        for key, label in roles.SOCIAL_PLATFORMS:
            last = (db.query(models.SocialStat)
                    .filter(models.SocialStat.platform == key)
                    .order_by(models.SocialStat.date.desc(),
                              models.SocialStat.id.desc()).first())
            if not last:
                continue
            # O'sish: 30 kun oldingi o'lchov bilan solishtiriladi
            was = (db.query(models.SocialStat)
                   .filter(models.SocialStat.platform == key,
                           models.SocialStat.date
                           <= last.date - timedelta(days=30))
                   .order_by(models.SocialStat.date.desc()).first())
            hint = last.date.isoformat() if last.date else None
            if was:
                d = last.followers - was.followers
                hint = (f"30 kunda {'+' if d >= 0 else ''}{d}"
                        + (f" · {hint}" if hint else ""))
            cards.append(_card(
                f"{label} obunachilar", last.followers, hint,
                "brand" if not was or last.followers >= was.followers
                else "amber", "/marketing"))
    except Exception:
        pass
    return cards

def _my_finance_cards(db: Session, user: models.User,
                      branch_id: int | None = None) -> list:
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
    # 2026-08-25: zina endi CHIZIQLI EMAS. Jahongir: "har bir
    # darajalar orasi 500XP bu juda oson bolib qolyabdi".
    # Yuqoriga chiqqan sari qadam kattalashadi (roles.ENG_LEVEL_POINTS).
    pts = int(points)
    idx = roles.level_index_for(pts)
    cur = roles.ENG_LEVELS[idx]
    is_last = idx >= len(roles.ENG_LEVELS) - 1
    lo = cur["need"]
    nxt = None if is_last else roles.ENG_LEVELS[idx + 1]
    hi = nxt["need"] if nxt else lo
    span = max(1, hi - lo)
    in_level = pts - lo
    return {
        "points": pts,
        "level": cur,
        "max_level": is_last,
        "level_from": lo,
        "level_to": None if is_last else hi,
        "next": None if is_last else {
            "label": nxt["label"], "ielts": nxt["ielts"], "cefr": nxt["cefr"],
            "points_left": max(0, hi - pts),
            "need": hi,
            "progress_percent": round(min(100.0, in_level * 100 / span), 1),
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
    # 2026-08-25: ILGARI har to'g'ri urinish 1 ball edi — bitta
    # so'zni qayta-qayta o'ynab ball yig'ib bo'lardi va shu sababli
    # "Lug'at 100" juda oson chiqardi. Endi ALOHIDA so'z sanaladi.
    vocab = (db.query(func.count(func.distinct(models.VocabAttempt.word_id)))
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
    # 2026-08-25: takroriy urinishlar emas, ALOHIDA so'z sanaladi —
    # aks holda bitta so'zni qayta-qayta o'ynab daraja ko'tarilardi.
    vocab = (db.query(func.count(func.distinct(models.VocabAttempt.word_id)))
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
    avail = _skill_available(db)
    skills = []
    for k in roles.SKILL_KEYS:
        pts = per_skill[k]
        score = roles.skill_score(pts)
        have = avail.get(k, 0)
        skills.append({
            "key": k,
            "label": roles.SKILL_LABELS[k],
            "tone": roles.SKILL_TONE[k],
            # 2026-08-25: 0-100 ball va IELTS band
            "score": score,
            "band": roles.ielts_band(score),
            "cefr": roles.score_cefr(score),
            # Mashq zaxirasi: bola hammasini yechib bo'lgan bo'lsa
            # "tepasi" bizning kontentimizga tiralgani ko'rinadi.
            "available": have,
            "coverage": (round(min(100.0, pts * 100 / have), 1)
                         if have else 0.0),
            **_level_for_points(pts),
        })
    bands = [x["band"] for x in skills]
    return {
        "overall": overall,
        "skills": skills,
        "ielts": {
            # Jahongir: "hamma skillarni qoshib ortachasini
            # chiqarganda uni IELTS balli kelib chiqsin"
            "band": roles.ielts_overall(bands),
            "skills": [{"key": x["key"], "label": x["label"],
                        "score": x["score"], "band": x["band"],
                        "cefr": x["cefr"]} for x in skills],
            "weakest": min(skills, key=lambda x: x["score"])["label"],
            "scale": [{"score": lo, "band": b}
                      for lo, b in roles.IELTS_BANDS],
        },
        "points_per_level": roles.PRACTICE_POINTS_PER_LEVEL,
        "levels": roles.ENG_LEVELS,
    }


# Mashq zaxirasi (har ko'nikmada nechta mashq BOR). Kontent kamdan-kam
# o'zgaradi — 10 daqiqaga keshlanadi, har so'rovda sanalmaydi.
_AVAIL_CACHE: dict = {"at": None, "data": None}


def _skill_available(db: Session) -> dict:
    from datetime import datetime as _dt
    now = _dt.utcnow()
    if (_AVAIL_CACHE["data"] is not None and _AVAIL_CACHE["at"]
            and (now - _AVAIL_CACHE["at"]).total_seconds() < 600):
        return _AVAIL_CACHE["data"]
    out = {k: 0 for k in roles.SKILL_KEYS}
    try:
        out["vocabulary"] = (db.query(func.count(models.VocabWord.id))
                             .filter(models.VocabWord.is_active == 1)
                             .scalar() or 0)
        gram = db.query(func.count(models.GrammarQuestion.id)).scalar() or 0
        out["grammar"] = gram
        rows = (db.query(models.PracticeItem.skill,
                         func.count(models.PracticeItem.id))
                .filter(models.PracticeItem.is_active == 1)
                .group_by(models.PracticeItem.skill).all())
        # ielts_* mashqlari ham o'z ko'nikmasiga sanaladi
        alias = {"ielts_listening": "listening", "ielts_reading": "reading"}
        for skill, cnt in rows:
            key = alias.get(skill, skill)
            if key in out:
                out[key] += int(cnt or 0)
        out["reading"] += (db.query(func.count(models.ReadingQuestion.id))
                           .scalar() or 0)
        # listening va writing mashqlari grammatika jumlalaridan ham
        # tuziladi — ular ham zaxiraga kiradi
        out["listening"] += gram
        out["writing"] += gram
    except Exception:
        db.rollback()
    _AVAIL_CACHE["at"] = now
    _AVAIL_CACHE["data"] = out
    return out

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
    """Brandbookdagi qoidalarni bazaga yozadi. Mavjudini o'zgartirmaydi.

    2026-08-14: bir marta bajarilgach BELGILANADI — ilgari har cold
    start'da 45 ta qator uchun 45 ta tekshiruv so'rovi ketardi."""
    if _seed_done(db, "brand_v1"):
        return
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
    _seed_mark(db, "brand_v1")

def _seed_kb(db: Session) -> None:
    """Boshlang'ich maqolalar — brandbookdan kelib chiqqan holda.
    Bir marta bajarilgach belgilanadi (sovuq start dietasi)."""
    if _seed_done(db, "kb_v1"):
        return
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
    _seed_mark(db, "kb_v1")

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
    """Bo'lim va lavozim ro'yxati. Bir marta yoziladi — ilgari har
    cold start'da 24 ta tekshiruv so'rovi ketardi (2026-08-14)."""
    if _seed_done(db, "hr_struct_v1"):
        return
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
    _seed_mark(db, "hr_struct_v1")

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

# =====================================================================
#  SUPPORT O'Z SOATI — BITTA MANBA (2026-09-10)
# =====================================================================
#  Jahongir: "Supportlarga asosiy dars vaqti korinyabdi men belgilagan
#  support soati emas" va keyin yana: "haliyam supportlarni oz darsi
#  vaqti emas asosiy dars vaqti korinyabdi".
#
#  Birinchi urinishda faqat "Guruhlarim" (/api/me/groups) tuzatilgan
#  edi. Lekin support kunlik ishini JONY TEACHER ilovasida qiladi
#  (/api/teacher/today, /week, /home, /support-options) — u yerda
#  vaqt hamon guruhning asosiy dars vaqtidan olinardi. Shuning uchun
#  qoida endi SHU YERDA, bitta joyda turadi va hamma ekran shundan
#  o'qiydi: yana bir ekran unutilib qolmasin.
#
#  Manba: SupportAssignment (days/start/end) — support menejer
#  biriktirganda tanlagan kun va soat.
SUPPORT_TIME_NOTE = ("Support vaqti belgilanmagan — support menejer "
                     "biriktirishi kerak")


def support_slot_map(db: Session, user):
    """Support uchun {group_id: {"days", "time"}}.

    Support BO'LMASA — None (ya'ni "guruhning o'z vaqti ishlatilsin")."""
    if getattr(user, "role", None) != roles.SUPPORT_TEACHER:
        return None
    out: dict = {}
    for a in (db.query(models.SupportAssignment)
              .filter(models.SupportAssignment.user_id == user.id,
                      models.SupportAssignment.group_id.isnot(None)).all()):
        if a.start and a.end:
            tm = f"{a.start}–{a.end}"
        else:
            tm = a.start or a.end or None
        prev = out.get(a.group_id)
        # Bir guruhga bir necha biriktiruv bo'lsa — vaqti borini olamiz
        if prev is None or (tm and not prev.get("time")):
            out[a.group_id] = {"days": a.days or None, "time": tm}
    return out


def group_time_for(slots, g):
    """(days, time, source, note).

    slots is None  -> oddiy ustoz/xodim: guruhning o'z dars vaqti.
    slots is dict  -> support: FAQAT biriktiruvdagi vaqt. Biriktiruvda
                      vaqt yo'q bo'lsa guruh vaqtiga tushib ketmaydi
                      (aynan shu chalkashlik shikoyatga sabab bo'lgan),
                      balki izoh chiqadi."""
    if slots is None:
        return (getattr(g, "lesson_days", None),
                getattr(g, "lesson_time", None), "group", None)
    s = slots.get(getattr(g, "id", None)) or {}
    tm = s.get("time")
    return (s.get("days"), tm, "support",
            None if tm else SUPPORT_TIME_NOTE)


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

def _resch_maps(db: Session, rows: list) -> dict:
    """TEZLIK (2026-08-23): dars ko'chirish ro'yxati uchun guruh, ustoz va
    qaror qabul qilgan xodim nomlarini UCHTA so'rovda oldindan yig'adi.

    Ilgari har qator uchun alohida uchta so'rov ketardi (200 qator =
    600 ta so'rov) va ro'yxat 2.5 soniyada ochilardi. Endi qatorlar
    soni qancha bo'lsa ham uchta so'rov."""
    gids = {r.group_id for r in rows if r.group_id}
    tids = {r.teacher_id for r in rows if r.teacher_id}
    uids = {r.decided_by for r in rows if r.decided_by}
    return {
        "g": {x.id: x for x in db.query(models.Group).filter(
            models.Group.id.in_(gids)).all()} if gids else {},
        "t": {x.id: x for x in db.query(models.Teacher).filter(
            models.Teacher.id.in_(tids)).all()} if tids else {},
        "u": {x.id: x for x in db.query(models.User).filter(
            models.User.id.in_(uids)).all()} if uids else {},
    }


def _resch_out(db: Session, r: models.LessonReschedule, maps=None) -> dict:
    # maps berilsa — bazaga qayta murojaat qilinmaydi (N+1 yo'q)
    if maps is not None:
        g = maps["g"].get(r.group_id)
        t = maps["t"].get(r.teacher_id) if r.teacher_id else None
        by = maps["u"].get(r.decided_by) if r.decided_by else None
    else:
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
    # HR ayirgan jarima ballari (2026-09-16)
    t = db.query(models.Teacher).get(teacher_id)
    adjs = []
    if t and t.user_id:
        adjs = (db.query(models.SupportAdjustment)
                .filter(models.SupportAdjustment.user_id == t.user_id,
                        models.SupportAdjustment.date >= start,
                        models.SupportAdjustment.date <= end)
                .order_by(models.SupportAdjustment.date,
                          models.SupportAdjustment.id).all())
    adj_total = round(sum(a.points or 0 for a in adjs), 2)
    calc = roles.support_salary(hours, students, pct, minus=adj_total)
    gnames = {g.id: g.name for g in db.query(models.Group)
              .filter(models.Group.id.in_(gids or [-1])).all()}
    formula = (f"({calc['hours']} soat x "
               f"{roles.SUPPORT_HOURS_W} + {calc['students']} "
               f"o'quvchi x {roles.SUPPORT_STUDENTS_W} + "
               f"koef {calc['coef']} x {roles.SUPPORT_RESULT_W}")
    if adj_total:
        formula += f" − {adj_total} jarima"
    formula += f") x {roles.SUPPORT_PAY_UNIT:,}"
    return {
        "period": f"{year:04d}-{month:02d}",
        "sessions": [_support_session_out(db, r) for r in rows],
        "session_count": len(rows),
        "groups": [{"id": i, "name": gnames.get(i)} for i in gids],
        **calc,
        "adjustments": [
            {"id": a.id, "date": a.date.isoformat(), "points": a.points,
             "reason": a.reason, "created_by": a.created_by}
            for a in adjs],
        "formula": formula.replace(",", " "),
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

def _ensure_month_charges(db: Session, budget_s: float = 8.0):
    """Har oyning 1-kuni ertalab 5:00 (Toshkent)dan boshlab faol
    o'quvchilardan shu oy to'lovi avtomat yechiladi.

    2026-08-14 (Jahongir: "Oylik avtomat hisoblash foydalanuvchi
    so'rovi ichida ishlaydi (30 soniya limit, guruhlar bo'ylab
    tsiklda). Guruhlar ko'paysa yarmida uzilib, oyning bir qismi
    hisoblanmay qolishi mumkin"):

      * BOSQICHMA-BOSQICH. Har GURUH alohida belgilanadi
        (mc_<oy>_g<id>). Vaqt byudjeti tugasa funksiya to'xtaydi —
        keyingi chaqiruvda AYNAN QOLGAN JOYIDAN davom etadi. Ilgari
        "birorta charge bormi?" degan yagona belgi bor edi: yarmida
        uzilsa, keyingi safar "bo'ldi" deb o'ylab to'xtardi va oyning
        qolgan qismi hech qachon hisoblanmasdi.
      * KIRISH SEKINLASHMAYDI. Login yo'lida byudjet kichik (8 s),
        kunlik cron'da katta (25 s) — 30 soniyalik Vercel limitiga
        hech qachon urilmaymiz.
      * POYGA HIMOYASI. pg_try_advisory_lock: ikkinchi nusxa kutib
        turmaydi, shunchaki chetga chiqadi (navbat yig'ilmasin).
      * IDEMPOTENT. Bir o'quvchidan bir oyda ikki marta yechilmaydi
        (already_charged + guruh belgisi).
    """
    import time as _time
    now = roles.local_now()
    today = now.date()
    if today.day == 1 and now.hour < 5:
        return
    period = f"{today.year:04d}-{today.month:02d}"
    dialect = ""
    try:
        dialect = db.get_bind().dialect.name
    except Exception:
        pass
    if dialect == "postgresql":
        try:
            got = db.execute(
                text("SELECT pg_try_advisory_lock(917201)")).scalar()
            if not got:
                return          # boshqa nusxa allaqachon ishlayapti
        except Exception:
            pass

    try:
        group_ids = [gid for (gid,) in
                     db.query(models.Student.group_id)
                     .filter(models.Student.status == "active",
                             models.Student.group_id.isnot(None))
                     .distinct().all()]
        # HAR GURUH alohida belgilanadi. Umumiy "bo'ldi" bayrog'i
        # ATAYLAB yo'q: oy o'rtasida ochilgan YANGI guruh ham
        # hisoblanishi kerak (eski kodda birinchi yechimdan keyin
        # funksiya butunlay to'xtardi va yangi guruh chetda qolardi).
        todo = [g for g in group_ids
                if not _seed_done(db, f"mc_{period}_g{g}")]
        if not todo:
            _purge_old_logs(db, today)
            return

        # Guruhlarni BITTA so'rovda olamiz (ilgari har biriga alohida
        # so'rov ketardi — 100 guruh = 100 so'rov).
        groups = {g.id: g for g in db.query(models.Group)
                  .filter(models.Group.id.in_(todo)).all()}

        t0 = _time.monotonic()
        for gid in todo:
            if _time.monotonic() - t0 > budget_s:
                continue        # keyingi chaqiruvda davom etadi
            g = groups.get(gid)
            gkey = f"mc_{period}_g{gid}"
            if not g:
                _seed_mark(db, gkey)    # guruh o'chgan — qayta urinmaymiz
                continue
            try:
                charges = billing.compute_student_charges(
                    db, g, today.year, today.month)
            except Exception:
                continue        # bu guruhni keyingi safar qayta uriniladi
            n = 0
            pending = 0        # hali yechilmagan, lekin yechilishi kerak
            for c in charges:
                if c.get("already_charged"):
                    continue
                if _charge_skipped(db, c["student_id"], period):
                    continue
                if (c.get("amount") or 0) <= 0:
                    # Hali dars o'tilmagan (oy boshi) — summa 0.
                    # Guruhni "tugadi" deb BELGILAMAYMIZ, darslar
                    # o'tilgach qayta ko'riladi.
                    pending += 1
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
            try:
                if n:
                    db.commit()
                # Guruhda yechilmagan qolmagan bo'lsagina belgilaymiz.
                # Belgi qo'yilgach bu guruh boshqa ko'rilmaydi —
                # ikki marta yechish yo'q; lekin kutayotgani bo'lsa
                # keyingi chaqiruvda davom etadi.
                if not pending:
                    _seed_mark(db, gkey)
            except Exception:
                db.rollback()
    finally:
        if dialect == "postgresql":
            try:
                db.execute(text("SELECT pg_advisory_unlock(917201)"))
                db.commit()
            except Exception:
                pass

    # Do'kondan olingan chegirmalar shu oy hisobiga tushsin (2026-08-15)
    try:
        _apply_shop_discounts(db, period)
    except Exception:
        db.rollback()

    _purge_old_logs(db, today)


# =====================================================================
#  JONY SHOP — COINGA CHEGIRMA (2026-08-15)
#  Jahongir: "oquvchilar o'z profilidan kirib Jony Shopda coiniga
#  skidka sotib olsa avtomat balansida shu narsa ozgarsin va
#  15-kungacha sotib olsa shu oy uchun 15-kundan keyin sotib olsa
#  keyingi oyga ishlasin".
#
#  QANDAY ISHLAYDI. Sotib olinganda Discount yozuvi ochiladi
#  (kind="coin_shop", period="YYYY-MM"). Chegirma pulga aylanishi
#  uchun O'SHA OYNING hisobi (charge) bo'lishi kerak:
#    - hisob allaqachon bor bo'lsa - balansga DARROV tushadi;
#    - hali bo'lmasa (keyingi oy) - hisob paydo bo'lgach kunlik
#      ish uni o'zi tushiradi.
#  Ikki marta tushmasligi applied_at belgisi bilan kafolatlanadi.
# =====================================================================
def _shop_discount_sum(db: Session, s, d) -> float:
    """Chegirma qancha so'm. Foiz bo'lsa - o'sha oydagi guruh
    narxidan hisoblanadi."""
    if d.amount:
        return float(d.amount)
    pct = float(d.percent or 0)
    if pct <= 0:
        return 0.0
    fee = 0.0
    try:
        if s.group is not None:
            fee = float(s.group.monthly_fee or 0)
            if not fee:
                fee = float((s.group.lesson_price or 0)
                            * (s.group.standard_lessons_per_month or 12))
    except Exception:
        fee = 0.0
    return round(fee * pct / 100.0, 0)


def _apply_shop_discounts(db: Session, period: str = None,
                          kind: str = "coin_shop") -> int:
    """Balansga tushirilmagan avtomat chegirmalarni tushiradi.
    Faqat o'sha oyning hisobi mavjud o'quvchilarga.

    kind — qaysi tur ("coin_shop" do'kon, "app_referral" do'st taklifi).
    Bitta yo'l ikkalasiga xizmat qiladi: balansga tushirish mantig'i
    ikki joyda takrorlanib, keyin bir-biridan uzoqlashib ketmasin."""
    q = (db.query(models.Discount)
         .filter(models.Discount.kind == kind,
                 models.Discount.status == "active",
                 models.Discount.applied_at.is_(None)))
    if period:
        q = q.filter(models.Discount.period == period)
    made = 0
    for d in q.all():
        if not d.period:
            continue
        s = db.query(models.Student).get(d.student_id)
        if s is None:
            continue
        charge = (db.query(models.Payment)
                  .filter(models.Payment.student_id == d.student_id,
                          models.Payment.period == d.period,
                          models.Payment.kind == "charge").first())
        if charge is None:
            continue            # hisob hali yo'q - keyingi safar
        amount = _shop_discount_sum(db, s, d)
        if amount <= 0:
            continue
        who = ("Do'st taklifi (avtomat)" if kind == "app_referral"
               else "Jony Shop (coin)")
        what = ("Do'st taklifi chegirmasi" if kind == "app_referral"
                else "Jony Shop chegirmasi")
        db.add(models.Payment(
            student_id=d.student_id, amount=abs(amount), kind="discount",
            period=d.period, created_by=who,
            note=f"{d.period} - {what} ({d.reason})"))
        d.applied_at = datetime.utcnow()
        made += 1
    if made:
        db.commit()
    return made


def backfill_student_branches(db: Session) -> int:
    """O'QUVCHINI O'Z FILIALIGA BIRIKTIRISH (2026-08-15).

    Jahongir: "yoqlamada bor lekin o'quvchilar royxatida o'quvchi
    korinmayabdiku".

    Sabab: eski ko'chirishdan qolgan 1600 dan ortiq o'quvchida filial
    UMUMAN belgilanmagan edi (branch_id bo'sh). Tepadagi tanlagichda
    biror filial tanlansa, bunday o'quvchi HECH QAYERDA ko'rinmasdi —
    ro'yxatda ham, qidiruvda ham, hisobotda ham. Yo'qlama esa guruh
    orqali ishlagani uchun u yerda ko'rinib turaverardi.

    Yechim: o'quvchi qaysi guruhda bo'lsa, o'sha guruhning filialiga
    biriktiriladi. Guruhi yo'q o'quvchiga tegilmaydi — uni qo'lda
    biriktirish kerak.

    Bir martalik va xavfsiz: faqat BO'SH filialni to'ldiradi,
    mavjudini hech qachon o'zgartirmaydi."""
    # Kuniga bir marta tekshiriladi (bir martalik emas): kelajakda
    # yana filialsiz o'quvchi paydo bo'lsa ham o'zi to'g'rilanadi.
    key = f"stbranch_{roles.local_today().isoformat()}"
    if _seed_done(db, key):
        return 0
    _seed_mark(db, key)
    n = 0
    try:
        rows = (db.query(models.Student, models.Group.branch_id)
                .join(models.Group,
                      models.Student.group_id == models.Group.id)
                .filter(models.Student.branch_id.is_(None),
                        models.Group.branch_id.isnot(None)).all())
        for st, bid in rows:
            st.branch_id = bid
            n += 1
        if n:
            db.commit()
    except Exception:
        db.rollback()
        return 0
    try:
        if n:
            audit.log(db, None, entity="student", action="update",
                      note=f"{n} ta o'quvchi o'z guruhining filialiga "
                           "biriktirildi (filial bo'sh edi)", commit=True)
    except Exception:
        db.rollback()
    return n


# =====================================================================
#  O'QUVCHI <-> GURUH BOG'LANISHI (2026-08-17)
#
#  Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi,
#  shuning uchun ham biz ham bazda 2ta gruppa qilishimiz kerak".
#
#  Student.group_id ("asosiy guruh") SAQLANIB QOLADI va shu yerdagi
#  birinchi faol bog'lanishga teng turadi — shunda mavjud kod
#  (hisob-kitob, yo'qlama, ustoz oyligi) buzilmaydi.
# =====================================================================

def in_group(group_id):
    """SQL sharti: o'quvchi shu guruhda (asosiy yoki qo'shimcha).

    Eski `Student.group_id == gid` o'rniga ishlatiladi — ikki guruhga
    qatnaydigan bola IKKALASIDA ham ko'rinsin. Asosiy guruh ham
    shartga kiritilgan: bog'lanish jadvali biror sababdan
    to'ldirilmay qolsa ham hech kim yo'qolib qolmaydi."""
    return or_(
        models.Student.group_id == group_id,
        models.Student.id.in_(
            select(models.StudentGroupLink.student_id).where(
                models.StudentGroupLink.group_id == group_id,
                models.StudentGroupLink.active == 1)),
    )


def student_group_ids(db: Session, student_id: int) -> list:
    """O'quvchining barcha FAOL guruhlari."""
    rows = (db.query(models.StudentGroupLink.group_id)
            .filter(models.StudentGroupLink.student_id == student_id,
                    models.StudentGroupLink.active == 1).all())
    return [g for (g,) in rows]


def sync_primary_group(db: Session, s) -> bool:
    """Student.group_id ni bog'lanishlarga moslashtiradi.

    Asosiy deb belgilangani bo'lsa — o'sha; bo'lmasa eng eski faol
    bog'lanish. Bittasi ham qolmasa — group_id bo'shatiladi."""
    links = (db.query(models.StudentGroupLink)
             .filter(models.StudentGroupLink.student_id == s.id,
                     models.StudentGroupLink.active == 1)
             .order_by(models.StudentGroupLink.is_primary.desc(),
                       models.StudentGroupLink.id).all())
    if not links:
        # XAVFSIZLIK (2026-08-17): bog'lanish jadvali hali
        # to'ldirilmagan bo'lsa (eski o'quvchi, cron ishlamagan)
        # group_id ni BO'SHATMAYMIZ — aks holda guruhi joyida
        # bo'lgan o'quvchi guruhsiz bo'lib qolardi. Buni
        # birlashtirish testi tutdi.
        return False
    want = links[0].group_id
    if s.group_id != want:
        s.group_id = want
        return True
    return False


def attach_group(db: Session, s, group_id: int, user=None,
                 joined=None, note: str = None):
    """O'quvchini guruhga qo'shish (bog'lanish yozuvi).

    Ikki marta qo'shilmaydi — bor bo'lsa qaytadan FAOLLASHTIRILADI,
    yangi qator ochilmaydi (tarix chalkashmasin)."""
    link = (db.query(models.StudentGroupLink)
            .filter(models.StudentGroupLink.student_id == s.id,
                    models.StudentGroupLink.group_id == group_id).first())
    if link:
        link.active = 1
        link.left_date = None
        if joined:
            link.joined_date = joined
    else:
        has = (db.query(models.StudentGroupLink)
               .filter(models.StudentGroupLink.student_id == s.id,
                       models.StudentGroupLink.active == 1).count())
        link = models.StudentGroupLink(
            student_id=s.id, group_id=group_id,
            is_primary=1 if has == 0 else 0,
            joined_date=joined or roles.local_today(),
            active=1, note=note,
            created_by=getattr(user, "full_name", None))
        db.add(link)
    db.flush()
    sync_primary_group(db, s)
    return link


def detach_group(db: Session, s, group_id: int, on=None) -> bool:
    """Guruhdan chiqarish — yozuv O'CHIRILMAYDI, yopiladi."""
    link = (db.query(models.StudentGroupLink)
            .filter(models.StudentGroupLink.student_id == s.id,
                    models.StudentGroupLink.group_id == group_id,
                    models.StudentGroupLink.active == 1).first())
    if not link:
        return False
    link.active = 0
    link.left_date = on or roles.local_today()
    link.is_primary = 0
    db.flush()
    sync_primary_group(db, s)
    return True


def ensure_link(db: Session, s) -> None:
    """group_id bor, lekin bog'lanish yozuvi yo'q bo'lsa — yaratadi.
    Birlashtirish va karta ochilishida ishlatiladi."""
    if not s or not s.group_id:
        return
    has = (db.query(models.StudentGroupLink)
           .filter(models.StudentGroupLink.student_id == s.id,
                   models.StudentGroupLink.group_id == s.group_id).first())
    if not has:
        db.add(models.StudentGroupLink(
            student_id=s.id, group_id=s.group_id, is_primary=1,
            joined_date=s.enrolled_date, active=1,
            created_by="Avtomat"))
        db.flush()


def backfill_student_groups(db: Session) -> int:
    """Mavjud group_id larni bog'lanish jadvaliga ko'chirish.

    Bir martalik. Hech narsa o'chirilmaydi — faqat yetishmayotgan
    bog'lanish qo'shiladi."""
    if _seed_done(db, "student_groups_v1"):
        return 0
    have = {(a, b) for a, b in db.query(
        models.StudentGroupLink.student_id,
        models.StudentGroupLink.group_id).all()}
    made = 0
    rows = (db.query(models.Student)
            .filter(models.Student.group_id.isnot(None)).all())
    for s in rows:
        if (s.id, s.group_id) in have:
            continue
        db.add(models.StudentGroupLink(
            student_id=s.id, group_id=s.group_id, is_primary=1,
            joined_date=s.enrolled_date, active=1,
            created_by="Avtomat ko'chirish"))
        made += 1
        if made % 500 == 0:
            db.commit()
    db.commit()
    _seed_mark(db, "student_groups_v1")
    return made


def fix_groupless_active(db: Session) -> int:
    """GURUHSIZ "FAOL" O'QUVCHI BO'LMASIN (2026-08-15).

    Jahongir: "birorta oquvchi guruhsiz lekin faol bola olmaydi
    guruhdan chiqarildimi u faol emas endi".

    Guruhi yo'q, lekin "faol" bo'lib qolgan o'quvchilar "Chiqib
    ketgan" holatiga o'tkaziladi — ular dars ham olmayapti, hisob
    ham yurmayapti, lekin faol sonini shishirib turardi.

    SINOVDAGILARGA TEGILMAYDI: yangi kelgan o'quvchi hali guruhga
    qo'shilmagan bo'lishi normal holat."""
    rows = (db.query(models.Student)
            .filter(models.Student.status == "active",
                    models.Student.group_id.is_(None)).all())
    if not rows:
        return 0
    for st in rows:
        st.status = roles.STUDENT_LEFT
    db.commit()
    try:
        audit.log(db, None, entity="student", action="update",
                  note=(f"{len(rows)} ta guruhsiz o'quvchi \"Chiqib "
                        "ketgan\" holatiga o'tkazildi (guruhsiz odam "
                        "faol bo'la olmaydi)"), commit=True)
    except Exception:
        db.rollback()
    return len(rows)


def _purge_old_logs(db: Session, today=None):
    """Eski kirish urinishlari va xato jurnalini tozalash — KUNIGA
    BIR MARTA (ilgari har chaqiruvda ikki DELETE ketardi)."""
    today = today or roles.local_today()
    key = f"purge_{today.isoformat()}"
    if _seed_done(db, key):
        return
    try:
        old = datetime.utcnow() - timedelta(days=30)
        db.query(models.LoginAttempt).filter(
            models.LoginAttempt.created_at < old).delete()
        db.query(models.ErrorLog).filter(
            models.ErrorLog.created_at < old).delete()
        # Eski bosqich belgilarini ham tozalab qo'yamiz (oylik
        # hisoblash har guruh uchun bitta belgi qoldiradi).
        keep = (today.replace(day=1) - timedelta(days=62)).strftime(
            "mc_%Y-%m")
        db.query(models.SeedMark).filter(
            models.SeedMark.key.like("mc_%"),
            models.SeedMark.key < keep).delete(
                synchronize_session=False)
        db.query(models.SeedMark).filter(
            models.SeedMark.key.like("purge_%"),
            models.SeedMark.key < "purge_"
            + (today - timedelta(days=7)).isoformat()).delete(
                synchronize_session=False)
        db.commit()
        _seed_mark(db, key)
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

def auto_freeze_notify(db, st: models.Student, group=None) -> dict:
    """AVTOMAT MUZLATILGANDA XABAR (2026-09-03).

    Jahongir: "keyin qaysidur o'quvchi avtomat muzlatilsa,
    o'qituvchiga xabar borsin, adminga ham xabar borsin".

    Ilgari avtomuzlatishda faqat administratorga jimgina vazifa
    tushardi. Ustoz esa umuman bilmasdi: bola ikki hafta
    ko'rinmay qolsa ham, ro'yxatdan chiqib ketgani unga hech
    qayerda aytilmasdi.

    Endi ikkalasiga ham xabar boradi:
      USTOZGA — o'z vazifalarida ko'rinadigan yozuv (guruh ustozi
                va, bo'lsa, biriktirilgan support ustoz);
      ADMINGA — o'sha filial administratoriga vazifa (bu qism
                _freeze_task orqali avvaldan bor edi).
    Telegram ulangan bo'lsa, ikkalasiga darrov xabar ham ketadi.

    Xabar MATNI ataylab qisqa va aniq: kim, qaysi guruh, nechta
    dars, va nima qilish kerak.

    Hech narsa majburiy emas: Telegram ulanmagan bo'lsa ham,
    ustozning akkaunti bo'lmasa ham amal to'xtamaydi — vazifa
    baribir qo'yiladi."""
    out = {"teacher_task": 0, "telegram": 0}
    gname = getattr(group, "name", None) or "guruh"
    day = roles.local_today()
    title = (f"Avtomuzlatildi: {st.full_name} — "
             f"{day.strftime('%d.%m.%Y')}")
    body = (f"{st.full_name} ({gname}) ketma-ket "
            f"{roles.AUTO_FREEZE_ABSENCES} darsga kelmadi va avtomat "
            f"MUZLATILDI. O'sha darslarning yo'qlamasi bekor qilindi "
            f"— ular oylikka kirmaydi.\n"
            f"O'quvchi endi davomat jadvalida chiqmaydi. Ota-onasi "
            f"bilan bog'lanib, sababini bilib bering — qaytadigan "
            f"bo'lsa administrator uni qayta faollashtiradi.")

    # --- USTOZ (va support ustoz) ---
    uids = []
    try:
        tid = getattr(group, "teacher_id", None)
        if tid:
            t = db.query(models.Teacher).get(tid)
            if t and t.user_id:
                uids.append(t.user_id)
        gid = getattr(group, "id", None)
        _SA = getattr(models, "SupportAssignment", None)
        if gid and _SA is not None:
            for a in db.query(_SA).filter(_SA.group_id == gid).all():
                sup_uid = getattr(a, "user_id", None)
                if sup_uid and sup_uid not in uids:
                    uids.append(sup_uid)
    except Exception:
        pass
    # DIQQAT: _hr_task_for() sarlavha bo'yicha dubl tekshiradi —
    # ustozga qo'yilgandan keyin supportga o'sha sarlavha bilan
    # ikkinchisi qo'yilmasdi. Shuning uchun bu yerda dubl HAR BIR
    # ODAM uchun alohida tekshiriladi: ikkalasi ham xabarni oladi,
    # lekin bir odamga ikki marta tushmaydi.
    for uid in uids:
        try:
            if db.query(models.Task).filter(
                    models.Task.title == title,
                    models.Task.assignee_id == uid).first():
                continue
            task = models.Task(
                title=title, description=body, assignee_id=uid,
                branch_id=st.branch_id,
                deadline=day + timedelta(days=2),
                priority="high", source="manual", created_by="Tizim")
            db.add(task)
            db.flush()
            _ensure_public_id(db, "task", task)
            out["teacher_task"] += 1
        except Exception:
            pass

    # --- TELEGRAM (ustoz + shu filial administratori) ---
    try:
        import notify
        if notify.enabled():
            who = list(uids)
            for u in (db.query(models.User)
                      .filter(models.User.role.in_(
                          [roles.ADMINISTRATOR, roles.SALES_MANAGER]),
                          models.User.is_active == 1,
                          models.User.branch_id == st.branch_id).all()):
                if u.id not in who:
                    who.append(u.id)
            text_ = f"JONYOS — AVTOMUZLATISH\n\n{body}"
            for u in (db.query(models.User)
                      .filter(models.User.id.in_(who or [-1]),
                              models.User.telegram_chat_id.isnot(None))
                      .all()):
                if notify.send(u.telegram_chat_id, text_):
                    out["telegram"] += 1
    except Exception:
        pass
    return out


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
        digits, variants = roles.phone_login(st.phone or st.parent_phone)
        if not digits:
            no_phone.append(st)
            continue
        if variants & taken:
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
        taken.update(variants)
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


# Seed belgilarini HAR BIRI uchun alohida so'rash o'rniga bir marta
# BITTA so'rovda o'qiymiz (2026-08-14 sovuq start dietasi). Jarayon
# xotirasida turadi; yangi belgi qo'yilsa shu yerga ham qo'shiladi.
_SEED_KEYS: set | None = None


def _seed_keys(db: Session) -> set:
    global _SEED_KEYS
    if _SEED_KEYS is None:
        try:
            _SEED_KEYS = {k for (k,) in db.query(models.SeedMark.key).all()}
        except Exception:
            return set()
    return _SEED_KEYS


def _seed_done(db: Session, key: str) -> bool:
    """Og'ir seed allaqachon to'liq bajarilganmi - so'rovsiz javob
    (belgilar ro'yxati bir marta o'qib olinadi)."""
    try:
        return key in _seed_keys(db)
    except Exception:
        return False


def _seed_mark(db: Session, key: str) -> None:
    """Seed to'liq bajarildi - keyingi startlarda ochilmasin."""
    try:
        if db.query(models.SeedMark).get(key) is None:
            db.add(models.SeedMark(key=key))
            db.commit()
        if _SEED_KEYS is not None:
            _SEED_KEYS.add(key)
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
    # USTOZ KARTASI HAM FAOL BO'LSIN (2026-09-03, Jahongir: "NUR
    # guruhidan Dostonni olib tashlay olmayabman"). Dostonbekning
    # akkaunti faol edi, lekin ustoz KARTASI 02.09 da yopilgan —
    # shuning uchun u tanlov ro'yxatiga chiqmasdi (ro'yxat kartadan
    # olinadi), bu tozalash esa faqat akkauntga qarab "sog'lom" deb
    # o'tkazib yuborardi. Endi ikkalasi ham tekshiriladi: karta
    # yo'q yoki yopiq bo'lsa — biriktirish bo'shatiladi.
    # Faqat YOPIQ karta stale hisoblanadi. Kartasi umuman yo'q eski
    # yozuvlarga tegilmaydi — ular haqida aniq ma'lumot yo'q.
    if ok:
        closed = {t.user_id for t in db.query(models.Teacher)
                  .filter(models.Teacher.user_id.in_(list(ok)),
                          models.Teacher.is_active == 0).all()}
        ok = ok - closed
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
    "schema_stamp",
    "models_fingerprint",
    "seal_schema",
    "_schema_ready",
    "ensure_tables",
    "_PERM_CACHE",
    "_activate_student",
    "_active_season",
    "_apply_reschedule",
    "_backfill_public_ids",
    "_book_out",
    "_branch_scope_ids",
    "_cabinet_groups",
    "support_slot_map",
    "group_time_for",
    "SUPPORT_TIME_NOTE",
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
    "_purge_old_logs",
    "backfill_student_branches",
    "fix_groupless_active",
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
    "in_group",
    "ensure_link",
    "student_group_ids",
    "sync_primary_group",
    "attach_group",
    "detach_group",
    "backfill_student_groups",
    "_apply_shop_discounts",
    "_shop_discount_sum",
    "_family_discount_percent",
    "_recharge_after_move",
    "_recharge_on_leave",
    "_norm_surname",
    "_close_request_tasks",
    "_notify_discount_approvers",
    "_notify_reschedule_approvers",
    "_same_surname",
    "_do_family_link",
    "_founder_name_fix",
    "_fraud_alert",
    "_freeze_task",
    "auto_freeze_notify",
    "_gam_card",
    "_in_user_branches",
    "_get_student_in_scope",
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
    "_payroll_branches",
    "_payroll_teacher_ids",
    "_earned_in_branches",
    "_paid_share",
    "_payroll_branch_label",
    "_salary_breakdown",
    "_check_pay_scope",
    "_pay_branch",
    "_period_bounds",
    "_period_key",
    "_perm_overrides",
    "_problem",
    "_raise_if_blocked",
    "_recalc_gamification",
    "_resch_maps",
    "_resch_out",
    "_reschedule_usage",
    "_rule_cap_hit",
    "_salary_card",
    "_finance_ledger",
    "_period_closed",
    "_seal_rows",
    "_seal_month",
    "_seal_closed_months",
    "_month_ledger",
    "_balance_split",
    "_month_name",
    "_month_title",
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
    "_skill_available",
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
    # 2026-08-27: __all__ ga qo'shilmagani uchun finance.py da
    # NameError chiqib, "Sotuv rejasi va bonus" tabi ochilmasdi.
    "_smm_sales_state",
    "_task_late",
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
    "partner_branch_ids",
    "test_branch_ids",
    "hidden_branch_ids",
    "blocked_branch_ids",
    "aggregate_skip_ids",
    "visible_branch_ids",
    "reset_partner_cache",
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

    # KIMGA VAZIFA TUSHADI (2026-09-06 auditi tuzatdi).
    # Ilgari faqat roles.ADMINISTRATOR qidirilardi. 2026-09-03 da
    # ikkita "Administrator" roli birlashtirilib, hamma xodim
    # SALES_MANAGER ga o'tkazilgan edi — natijada bayroq qo'yilardi,
    # lekin VAZIFA HECH KIMGA tushmasdi (jimgina yo'qolardi).
    _ADMIN_ROLES_RISK = (roles.SALES_MANAGER, roles.ADMINISTRATOR)
    admins: dict = {}
    for u in (db.query(models.User)
              .filter(models.User.role.in_(_ADMIN_ROLES_RISK),
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
