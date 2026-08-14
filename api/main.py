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

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
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

# ---- entry.py ("M.xxx" / "from main import ...") mos kelishi uchun
# qayta eksport - nomlar boshqa fayllarga ko'chgan, lekin entry.py hali
# ularni `main` modulidan kutadi. ----
from auth_users import _guard_role_assignment, _smm_new_staff_task, _sync_user_branches
from branches_rooms import _room_out
from common import _cleanup_stale_support_assignments, _branch_in, _in_user_branches, _charge_from_activation, _charge_skipped, _check_enrolment, _check_teacher_load, _ensure_public_id, _ensure_teacher_card, _get_group_in_scope, _group_students, _hr_task_for, _lessons_left_in_month, _period_key, _raise_if_blocked, _student_discount_percent, _support_month, _sync_student_left_date, _teacher_of_user, _time_to_min, _utc_window, backfill_missing_ids, scope_to_branch, student_balance
from dashboard import _collection_bonus, _first_payment_dates, _new_client_bonus, _payment_first_dates, admin_kpi
from groups_lessons import _sync_scheduled_lessons
from inventory import _check_stock
from me import _my_teacher_or_404
from support import _days_uz, _support_conflicts
from timetable import require_perm
from common import _ensure_month_charges
from content import _period_range, _smm_kpi

# SOVUQ START: sxema allaqachon joriy versiyada bo'lsa, 143 ta
# jadval uchun reflection so'rovlari YUBORILMAYDI — bitta yengil
# "stamp bormi?" so'rovi bilan cheklanamiz (2026-08-14).
from common import _schema_bootstrap, _schema_ready  # noqa: E402

if not _schema_ready():
    Base.metadata.create_all(bind=engine)
    _schema_bootstrap()

app = FastAPI(title="JonyOS API — Jony Academy boshqaruv tizimi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 2026-08: main.py bo'lindi (27 205 qator edi) - har bir domen o'z faylida
# (routers/*.py), umumiy yordamchi funksiyalar common.py'da. Xatti-harakat
# o'zgarmagan - faqat joylashuv. Qarang: REFACTOR_NOTES.md
# ---------------------------------------------------------------------------
import academic as _r_academic
import audit_admin as _r_audit_admin
import auth_users as _r_auth_users
import branches_rooms as _r_branches_rooms
import complaints as _r_complaints
import content as _r_content
import dashboard as _r_dashboard
import examiners as _r_examiners
import exams as _r_exams
import finance as _r_finance
import gamification as _r_gamification
import groups_lessons as _r_groups_lessons
import hr as _r_hr
import hr_ats as _r_hr_ats
import inventory as _r_inventory
import leads as _r_leads
import marketing as _r_marketing
import me as _r_me
import notifications as _r_notifications
import nps as _r_nps
import parents as _r_parents
import student_app as _r_student_app
import students as _r_students
import support as _r_support
import system as _r_system
import tasks as _r_tasks
import teacher_app as _r_teacher_app
import teachers as _r_teachers
import timetable as _r_timetable

app.include_router(_r_academic.router)
app.include_router(_r_audit_admin.router)
app.include_router(_r_auth_users.router)
app.include_router(_r_branches_rooms.router)
app.include_router(_r_complaints.router)
app.include_router(_r_content.router)
app.include_router(_r_dashboard.router)
app.include_router(_r_examiners.router)
app.include_router(_r_exams.router)
app.include_router(_r_finance.router)
app.include_router(_r_gamification.router)
app.include_router(_r_groups_lessons.router)
app.include_router(_r_hr.router)
app.include_router(_r_hr_ats.router)
app.include_router(_r_inventory.router)
app.include_router(_r_leads.router)
app.include_router(_r_marketing.router)
app.include_router(_r_me.router)
app.include_router(_r_notifications.router)
app.include_router(_r_nps.router)
app.include_router(_r_parents.router)
app.include_router(_r_student_app.router)
app.include_router(_r_students.router)
app.include_router(_r_support.router)
app.include_router(_r_system.router)
app.include_router(_r_tasks.router)
app.include_router(_r_teacher_app.router)
app.include_router(_r_teachers.router)
app.include_router(_r_timetable.router)

# ---- Fon vazifalari: dastlabki ma'lumotlarni urug'lantirish (idempotent) ----
try:
    from sqlalchemy.orm import Session as _GS
    from gamification import _seed_gamification
    from exams import _seed_rubrics
    from notifications import _seed_replies
    with _GS(engine) as _db:
        _seed_gamification(_db)
        _seed_rubrics(_db)
        _seed_replies(_db)
except Exception:
    pass
try:
    from sqlalchemy.orm import Session as _BS
    from common import _seed_brand, _seed_kb, _link_teacher_accounts
    with _BS(engine) as _db2:
        _seed_brand(_db2)
        _seed_kb(_db2)
        _link_teacher_accounts(_db2)
except Exception:
    pass
try:
    from sqlalchemy.orm import Session as _HS
    from common import _seed_hr_structure
    with _HS(engine) as _db3:
        _seed_hr_structure(_db3)
except Exception:
    pass
# Jony Student: lug'at o'yinlari birinchi kundanoq ishlashi uchun
# boshlang'ich so'z bazasi (idempotent — dublikat yaratmaydi).
try:
    from sqlalchemy.orm import Session as _VS
    from vocab_seed import seed_vocab
    with _VS(engine) as _db4:
        seed_vocab(_db4)
except Exception:
    pass

# Grammar savollar bazasi (idempotent - faqat yo'qlarini qo'shadi)
try:
    from sqlalchemy.orm import Session as _VS7
    from grammar_seed import seed_grammar
    with _VS7(engine) as _db7:
        seed_grammar(_db7)
except Exception:
    pass

# Grammar A2/B1/B2 + A1 qolgan cloze (2026-08-12, Jahongir: "A2, B1,
# B2 uchun tuzilma tayyor, kontent YO'Q - shularni to'ldirib chiq
# hammasini. A1'dagi cloze ham"). Idempotent (grammar_l2_v1).
try:
    from sqlalchemy.orm import Session as _VS13
    from grammar_seed2 import seed_grammar_levels
    with _VS13(engine) as _db13:
        seed_grammar_levels(_db13)
except Exception:
    pass

# 4 ko'nikma yangi mashq turlari (idempotent)
try:
    from sqlalchemy.orm import Session as _VS9
    from practice_seed import seed_practice
    with _VS9(engine) as _db9:
        seed_practice(_db9)
except Exception:
    pass

# Reading matnlari (idempotent)
try:
    from sqlalchemy.orm import Session as _VS8
    from reading_seed import seed_reading
    with _VS8(engine) as _db8:
        seed_reading(_db8)
except Exception:
    pass

# TEZLIK: coin importlari va idempotent tekshiruvlar uchun indeks
# (source, ref_id) - usiz har startupda katta skanerlash bo'lardi.
# IF NOT EXISTS - mavjud bo'lsa hech narsa qilmaydi, ma'lumotga
# tegmaydi (Postgres ham, SQLite ham qo'llaydi).
try:
    from sqlalchemy import text as _sql_text
    with engine.connect() as _conn:
        _conn.execute(_sql_text(
            "CREATE INDEX IF NOT EXISTS ix_coin_source_ref "
            "ON coin_entries (source, ref_id)"))
        _conn.commit()
except Exception:
    pass

# Eski (Crystal) tizimdagi coin tarixi - idempotent, ism bo'yicha,
# arxivdagilarga ham; topilmaganlar shunchaki o'tkaziladi (Jahongir)
try:
    from sqlalchemy.orm import Session as _VS13
    from legacy_coin_seed import seed_legacy_coins
    with _VS13(engine) as _db13:
        seed_legacy_coins(_db13)
except Exception:
    pass

# Coin do'koni xaridlari (LC UP daromadlar eksporti) - coin yechish;
# eski eksportda allaqachon aks etganlari qayta kiritilmaydi
try:
    from sqlalchemy.orm import Session as _VS14
    from legacy_shop_seed import seed_legacy_shop
    with _VS14(engine) as _db14:
        seed_legacy_shop(_db14)
except Exception:
    pass

# LC UP joriy balanslari bilan YAKUNIY tenglashtirish - barcha coin
# importlaridan KEYIN turishi shart (Jahongir, 2026-08-11 snapshot)
try:
    from sqlalchemy.orm import Session as _VS15
    from lcup_balance_seed import seed_lcup_balance
    with _VS15(engine) as _db15:
        seed_lcup_balance(_db15)
except Exception:
    pass

# Muzlatilganlarning eski "kelmadi" yo'qlamalarini tozalash -
# kelmagan o'quvchi uchun ustozga oylik hisoblanmasin (Jahongir)
try:
    from sqlalchemy.orm import Session as _VS12
    from common import _cleanup_frozen_absences
    with _VS12(engine) as _db12:
        _cleanup_frozen_absences(_db12)
except Exception:
    pass

# 2026-08-11 (Jahongir): "men Bekobod 1 uchun reja tuzgan edim, lekin
# u Bekobod 2 ga ham o'tib qolibdi" - eski (filialsiz) reja yozuvlari
# bir marta Bekobod 1 ga biriktiriladi, reja endi filial kesimida
try:
    from sqlalchemy.orm import Session as _VS16
    from common import _seed_done, _seed_mark
    with _VS16(engine) as _db16:
        if not _seed_done(_db16, "plan_branch_v1"):
            _bb1 = (_db16.query(models.Branch)
                    .filter(models.Branch.name.ilike("bekobod 1%"))
                    .first())
            if _bb1 is not None:
                (_db16.query(models.PlanTarget)
                 .filter(models.PlanTarget.branch_id.is_(None))
                 .update({models.PlanTarget.branch_id: _bb1.id},
                         synchronize_session=False))
                _db16.commit()
            _seed_mark(_db16, "plan_branch_v1")
except Exception:
    pass

# Eski yillardagi to'lov yig'ilishi (reja/fakt) arxivi - idempotent
try:
    from sqlalchemy.orm import Session as _VS11
    from legacy_collection_seed import seed_legacy_collection
    with _VS11(engine) as _db11:
        seed_legacy_collection(_db11)
except Exception:
    pass

# Eski tizimdagi ustozlar dars-sifati statistikasi (2026 yan-iyul).
# Jahongir: "qolda kirigizib otirish keremas" - avtomat import,
# rubric_key bo'yicha idempotent.
try:
    from sqlalchemy.orm import Session as _VS10
    from legacy_quality_seed import seed_legacy_quality
    with _VS10(engine) as _db10:
        seed_legacy_quality(_db10)
except Exception:
    pass

# Barcha mavjud o'quvchilarga akkaunt: login = telefon, parol =
# jonyjony (2026-08-10, Jahongir). Yangi kiritilganlarga
# _ensure_student_account ochadi - bu esa eskilarni bir marta qoplaydi.
try:
    from sqlalchemy.orm import Session as _VS6
    from common import _backfill_student_accounts
    with _VS6(engine) as _db6:
        _backfill_student_accounts(_db6)
except Exception:
    pass

# Sug'diyona Toshtemirovaning DUBLIKAT kartasini birlashtirib o'chirish.
# Jahongir (2026-08-12): "Shu ketgan sugdiyonani o'chirib tashla,
# duplikat umuman qolmasin". Xavfsiz yo'l: avval dublikatga tegishli
# BARCHA yozuvlar (darslar, yo'qlamalar orqali oylik, kuzatuvlar,
# filiallar...) faol kartaga ko'chiriladi, keyin bo'sh qolgan dublikat
# o'chiriladi - hech qanday ma'lumot yo'qolmaydi. Bir martalik.
try:
    from sqlalchemy.orm import Session as _VS12
    from common import _seed_done, _seed_mark
    from legacy_quality_seed import _norm as _lqnorm
    with _VS12(engine) as _db12:
        if not _seed_done(_db12, "merge_dup_sugdiyona_v1"):
            def _key(nm):
                return " ".join(sorted(_lqnorm(x) for x in (nm or "").split()
                                       if _lqnorm(x)))
            _want = _key("Sug'diyona Toshtemirova")
            _cands = [t for t in _db12.query(models.Teacher).all()
                      if _key(t.full_name) == _want]
            _alive = [t for t in _cands if not t.left_date]
            _gone = [t for t in _cands if t.left_date]
            if len(_alive) == 1 and len(_gone) == 1:
                _main, _dup = _alive[0], _gone[0]
                for _tbl in Base.metadata.tables.values():
                    if _tbl.name == "teachers":
                        continue
                    if _tbl.name == "teacher_branches":
                        # takror (ustoz, filial) juftlik qolmasin
                        _have = {r[0] for r in _db12.execute(
                            _tbl.select().with_only_columns(
                                _tbl.c.branch_id).where(
                                _tbl.c.teacher_id == _main.id)).all()}
                        _db12.execute(_tbl.delete().where(
                            (_tbl.c.teacher_id == _dup.id)
                            & (_tbl.c.branch_id.in_(_have or [-1]))))
                    # teachers.id ga qaragan HAR QANDAY ustun
                    # (teacher_id, substitute_teacher_id, ...)
                    for _col in _tbl.c:
                        if any(_fk.column.table.name == "teachers"
                               for _fk in _col.foreign_keys):
                            _db12.execute(_tbl.update().where(
                                _col == _dup.id
                            ).values({_col.name: _main.id}))
                # Dublikatning alohida akkaunti bo'lsa - o'chirmaymiz,
                # faqat kirishini yopamiz (ma'lumot yo'qolmasin).
                if _dup.user_id and _dup.user_id != _main.user_id:
                    _u = _db12.query(models.User).get(_dup.user_id)
                    if _u:
                        _u.is_active = 0
                _db12.delete(_dup)
                _db12.commit()
                try:
                    audit.log(_db12, None, entity="teacher",
                              action="merge_duplicate",
                              entity_id=_main.id,
                              entity_label=_main.full_name,
                              note=(f"Dublikat karta #{_dup.id} "
                                    f"('{_dup.full_name}') faol kartaga "
                                    f"birlashtirilib o'chirildi"),
                              commit=True)
                except Exception:
                    _db12.rollback()
            _seed_mark(_db12, "merge_dup_sugdiyona_v1")
except Exception:
    pass

# IKKI LAVOZIMLI XODIMLAR (2026-08-12, Jahongir): "Nodir Abdulatipov
# ham ustoz ham filial rahbari... Go'zal Zoxidova ham ustoz ham o'quv
# bo'limi rahbari - lavozim almashtirish funksiyasi berilsin".
# - Nodir: asosiy lavozim filial rahbari, qo'shimcha - ustoz.
# - Go'zal: IKKITA alohida akkauntda edi (5: o'quv bo'limi, 49: ustoz).
#   Ustoz kartasi asosiy (o'quv bo'limi) akkauntiga ulanadi, vazifalar
#   ko'chiriladi, eski ustoz-akkaunt faolsizlantiriladi (o'chirilmaydi).
# Bir martalik, hech qanday ma'lumot yo'qolmaydi.
try:
    from sqlalchemy.orm import Session as _VS14
    from common import _seed_done as _sd14, _seed_mark as _sm14
    from legacy_quality_seed import _norm as _n14
    with _VS14(engine) as _db14:
        if not _sd14(_db14, "dual_role_setup_v1"):
            def _key14(nm):
                return " ".join(sorted(_n14(x) for x in (nm or "").split()
                                       if _n14(x)))

            def _find_user(name_key, role):
                return [u for u in _db14.query(models.User).all()
                        if _key14(u.full_name) == name_key
                        and u.role == role]

            def _add_extra(uid, role):
                have = _db14.query(models.UserRole).filter(
                    models.UserRole.user_id == uid,
                    models.UserRole.role == role).count()
                if not have:
                    _db14.add(models.UserRole(user_id=uid, role=role))

            # ---- Nodir: teacher -> branch_manager (+ teacher) ----
            _nk = _key14("Nodirbek Abdulatipov")
            _nods = _find_user(_nk, roles.TEACHER)
            if len(_nods) == 1:
                _u = _nods[0]
                _u.role = roles.BRANCH_MANAGER
                _add_extra(_u.id, roles.TEACHER)
                try:
                    audit.log(_db14, None, entity="user",
                              action="role_change", entity_id=_u.id,
                              entity_label=_u.full_name,
                              old_value="teacher",
                              new_value="branch_manager (+ustoz)",
                              note="Ikki lavozim: tepadagi/profildagi "
                                   "tanlagichdan almashtiriladi")
                except Exception:
                    pass

            # ---- Go'zal: 2 akkauntni birlashtirish ----
            _gk = _key14("Go'zal Zohidova")
            _mains = _find_user(_gk, roles.ACADEMIC_HEAD)
            _dups = _find_user(_gk, roles.TEACHER)
            if len(_mains) == 1 and len(_dups) == 1:
                _m, _d = _mains[0], _dups[0]
                # Ustoz kartasi asosiy akkauntga
                for _t in _db14.query(models.Teacher).filter(
                        models.Teacher.user_id == _d.id).all():
                    _t.user_id = _m.id
                # Vazifalar ko'chadi
                (_db14.query(models.Task)
                 .filter(models.Task.assignee_id == _d.id)
                 .update({models.Task.assignee_id: _m.id},
                         synchronize_session=False))
                (_db14.query(models.Task)
                 .filter(models.Task.watcher_id == _d.id)
                 .update({models.Task.watcher_id: _m.id},
                         synchronize_session=False))
                _add_extra(_m.id, roles.TEACHER)
                _d.is_active = 0
                try:
                    audit.log(_db14, None, entity="user",
                              action="merge_accounts", entity_id=_m.id,
                              entity_label=_m.full_name,
                              note=f"Ustoz-akkaunt (#{_d.id}, "
                                   f"{_d.username}) asosiy akkauntga "
                                   f"birlashtirildi va faolsizlantirildi")
                except Exception:
                    pass
            _db14.commit()
            _sm14(_db14, "dual_role_setup_v1")
except Exception:
    pass

# Onlayn arizalar quvurda ham ko'rinsin (bir martalik backfill)
try:
    from sqlalchemy.orm import Session as _VS15
    from hr_ats import backfill_apply_applications
    with _VS15(engine) as _db15:
        backfill_apply_applications(_db15)
        from hr_ats import fix_apply_attachments
        fix_apply_attachments(_db15)
except Exception:
    pass

# Eski (2026-08-12 gacha yuborilgan) chegirma so'rovlari hech kimga
# vazifa bo'lib tushmagan edi - Jahongir: "menga kelmadi lekin".
# Bir martalik: kutib yotgan so'rovlarga tasdiqlovchilar uchun vazifa
# ochib qo'yamiz, shunda ular ko'zdan qolmaydi.
try:
    from sqlalchemy.orm import Session as _VS16
    from common import (_seed_done as _sd16, _seed_mark as _sm16,
                        _notify_discount_approvers as _nda16)
    with _VS16(engine) as _db16:
        if not _sd16(_db16, "disc_pending_task_v1"):
            for _d16 in _db16.query(models.Discount).filter(
                    models.Discount.status == "pending").all():
                _st16 = _db16.query(models.Student).get(_d16.student_id)
                if _st16:
                    try:
                        _nda16(_db16, _d16, _st16)
                    except Exception:
                        pass
            _sm16(_db16, "disc_pending_task_v1")
except Exception:
    pass

# Ishdan bo'shatilgan supportlarning guruhdagi izlarini tozalash.
# Tuzatishdan OLDIN bo'shatilganlar uchun (masalan Malika) - keyingilari
# bo'shatish paytidayoq _release_support_groups orqali tozalanadi.
try:
    from sqlalchemy.orm import Session as _VS5
    with _VS5(engine) as _db5:
        _cleanup_stale_support_assignments(_db5)
except Exception:
    pass


@app.exception_handler(Exception)
async def _unhandled_error(request: Request, exc: Exception):
    """Kutilmagan xato: foydalanuvchi aytishini kutmasdan error_logs
    jadvaliga yozamiz - asoschi Audit bo'limida ko'radi."""
    try:
        import traceback
        edb = SessionLocal()
        edb.add(models.ErrorLog(
            path=str(request.url.path)[:200],
            method=request.method,
            detail="".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__))[-4000:],
        ))
        edb.commit()
        edb.close()
    except Exception:
        pass
    return JSONResponse(status_code=500, content={
        "detail": "Serverda kutilmagan xato. Bu xato qayd etildi va "
                  "tez orada ko'rib chiqiladi."})
