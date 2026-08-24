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
import advisor as _r_advisor
import level_test as _r_level_test
import audit_admin as _r_audit_admin
import backup as _r_backup
import courses as _r_courses
import selftest as _r_selftest
import demo_seed as _r_demo_seed
import guide as _r_guide
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
app.include_router(_r_advisor.router)
app.include_router(_r_level_test.router)
app.include_router(_r_audit_admin.router)
app.include_router(_r_backup.router)
app.include_router(_r_courses.router)
app.include_router(_r_selftest.router)
app.include_router(_r_demo_seed.router)
app.include_router(_r_guide.router)
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

# IELTS listening: spelling / raqam / postcode (2026-08-24)
try:
    from sqlalchemy.orm import Session as _VS15
    from ielts_seed import seed_ielts
    with _VS15(engine) as _db15:
        seed_ielts(_db15)
except Exception:
    pass

# IELTS listening 2-blok: ma'lumot ilib olish + tuzoqlar (2026-08-24)
try:
    from sqlalchemy.orm import Session as _VS16
    from ielts_seed2 import seed_ielts2
    with _VS16(engine) as _db16:
        seed_ielts2(_db16)
except Exception:
    pass

# IELTS listening 3-blok: exact word trap (2026-08-24)
try:
    from sqlalchemy.orm import Session as _VS17
    from ielts_seed3 import seed_ielts3
    with _VS17(engine) as _db17:
        seed_ielts3(_db17)
except Exception:
    pass

# C1/C2 ingliz + ru/de/ko grammatika (2026-08-24, idempotent)
try:
    from sqlalchemy.orm import Session as _VS14
    from grammar_seed3 import seed_grammar_extra
    with _VS14(engine) as _db14:
        seed_grammar_extra(_db14)
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

# O'quvchi filiali bo'sh bo'lsa - guruhining filialiga biriktiramiz
# (2026-08-15: "yoqlamada bor lekin o'quvchilar royxatida yo'q")
try:
    from sqlalchemy.orm import Session as _VS18
    from common import (backfill_student_branches as _bsb,
                        fix_groupless_active as _fga)
    with _VS18(engine) as _db18:
        _bsb(_db18)
        _fga(_db18)
except Exception:
    pass

# Nomzodning lavozimi va fani izoh matnidan alohida maydonga
# ko'chirilsin (bir martalik, 2026-08-15)
try:
    from sqlalchemy.orm import Session as _VS17
    from hr_ats import backfill_candidate_positions as _bcp
    with _VS17(engine) as _db17:
        _bcp(_db17)
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



# =====================================================================
#  XATO OGOHLANTIRISHI (2026-08-15)
#  Kutilmagan server xatosi yuz berishi bilan asoschiga Telegram
#  xabar ketadi. Bir xil xato 30 daqiqada bir marta - telefon
#  xabarga ko'milib qolmasin.
# =====================================================================
_ALERT_SEEN: dict = {}
_ALERT_QUIET_MIN = 30


def _alert_founders(db, path: str, method: str, who, trace: str) -> bool:
    import notify
    if not notify.enabled():
        return False
    last_line = (trace.strip().splitlines() or ["?"])[-1][:200]
    key = f"{method} {path} :: {last_line}"
    now = datetime.utcnow()
    seen = _ALERT_SEEN.get(key)
    if seen and (now - seen).total_seconds() < _ALERT_QUIET_MIN * 60:
        return False
    _ALERT_SEEN[key] = now
    if len(_ALERT_SEEN) > 200:          # xotira o'smasin
        _ALERT_SEEN.clear()
        _ALERT_SEEN[key] = now

    when = roles.to_local(now).strftime("%d.%m.%Y %H:%M")
    text_ = (
        "JONYOS - SERVER XATOSI\n"
        f"Vaqt: {when}\n"
        f"Manzil: {method} {path}\n"
        f"Kim duch keldi: {who or 'nomalum'}\n\n"
        f"{last_line}\n\n"
        "To'liq matn: JonyOS -> Audit -> Tizim xatolari.\n"
        f"(Bir xil xato {_ALERT_QUIET_MIN} daqiqada bir marta "
        "yuboriladi.)")
    sent = 0
    try:
        for u in (db.query(models.User)
                  .filter(models.User.role == roles.FOUNDER,
                          models.User.is_active == 1,
                          models.User.telegram_chat_id.isnot(None)).all()):
            if notify.send(u.telegram_chat_id, text_):
                sent += 1
    except Exception:
        return False
    return bool(sent)


@app.exception_handler(Exception)
async def _unhandled_error(request: Request, exc: Exception):
    """Kutilmagan xato: foydalanuvchi aytishini kutmasdan error_logs
    jadvaliga yozamiz - asoschi Audit bo'limida ko'radi.

    2026-08-15 (Jahongir: "Xato monitoringi ... buzilganini xodim
    qo'ng'iroq qilganda bilasiz"): endi xato yuz bergan zahoti
    ASOSCHIGA TELEGRAM XABAR ham ketadi. Yangi sekret kerak emas -
    TELEGRAM_BOT_TOKEN allaqachon serverda bor.

    BOSIB TURISH: bir xil xato (bir xil manzil + bir xil oxirgi
    satr) 30 daqiqada BIR MARTA yuboriladi. Aks holda bitta buzilgan
    sahifa telefonni xabarga ko'mib tashlardi."""
    import traceback
    trace = "".join(traceback.format_exception(
        type(exc), exc, exc.__traceback__))
    path = str(request.url.path)[:200]
    who = None
    edb = None
    try:
        edb = SessionLocal()
        # Kim duch keldi - xatoni takrorlash uchun eng muhim ma'lumot
        try:
            tok = (request.headers.get("authorization") or "").replace(
                "Bearer ", "")
            if tok:
                from jose import jwt as _jwt
                from auth import ALGORITHM as _alg
                sub = _jwt.decode(tok, SECRET_KEY,
                                  algorithms=[_alg]).get("sub")
                u = edb.query(models.User).filter(
                    models.User.username == sub).first()
                who = u.full_name if u else sub
        except Exception:
            who = None
        edb.add(models.ErrorLog(
            path=path, method=request.method, user_name=who,
            detail=trace[-4000:]))
        edb.commit()
    except Exception:
        try:
            if edb is not None:
                edb.rollback()
        except Exception:
            pass

    # ---- Asoschiga darhol xabar ----
    try:
        if edb is not None:
            _alert_founders(edb, path, request.method, who, trace)
    except Exception:
        pass
    try:
        if edb is not None:
            edb.close()
    except Exception:
        pass

    return JSONResponse(status_code=500, content={
        "detail": "Serverda kutilmagan xato. Bu xato qayd etildi va "
                  "tez orada ko'rib chiqiladi."})


# ---------------------------------------------------------------------
# LIGA COINLARINI YANGI SHKALAGA TENGLASHTIRISH (2026-08-20).
# Jahongir: "eski tartiba olingan coinlarni yangi tartibdagidek qilib
# berish kerak". Eski shkala (amateur 1 ... goat 100) bo'yicha berilgan
# har bir liga-coin yozuvi yangi shkala (1,2,3,4,5,6,8,10,12,14,16,25,
# 30) bilan solishtiriladi va FARQ bitta tuzatish yozuvi bo'lib
# qo'shiladi. Eski yozuvlar O'CHIRILMAYDI - tarix to'liq qoladi.
# Balans 0 dan pastga tushmaydi (coinini sarflab bo'lganlarga qarz
# yozilmaydi). Bir martalik.
try:
    from sqlalchemy.orm import Session as _VS17
    from common import _seed_done as _sd17, _seed_mark as _sm17
    from common import _student_coin_balance as _bal17
    with _VS17(engine) as _db17:
        if not _sd17(_db17, "league_coin_rescale_v1"):
            _new_scale = {lg.key: (lg.reward_coin or 0)
                          for lg in _db17.query(models.XpLeague).all()}
            _name2key = {lg.name: lg.key
                         for lg in _db17.query(models.XpLeague).all()}
            _rows17 = (_db17.query(models.CoinEntry)
                       .filter(models.CoinEntry.source == "league").all())
            _delta = {}
            for _e in _rows17:
                _nm = (_e.note or "").split(" ligasiga")[0].strip()
                _k = _name2key.get(_nm)
                if not _k:
                    continue
                _d = _new_scale.get(_k, 0) - (_e.amount or 0)
                if _d:
                    _delta[_e.student_id] = _delta.get(_e.student_id, 0) + _d
            _fixed17 = 0
            _note17 = ("Liga coinlari yangi shkalaga tenglashtirildi "
                       "(2026-08-20 qoidasi)")
            for _sid, _d in _delta.items():
                if not _d:
                    continue
                # Ikki lambda bir vaqtda uyg'onsa ham takror yozmasin
                if (_db17.query(models.CoinEntry)
                        .filter(models.CoinEntry.student_id == _sid,
                                models.CoinEntry.note == _note17)
                        .first()):
                    continue
                if _d < 0:
                    _have = _bal17(_db17, _sid)
                    if _have + _d < 0:
                        _d = -_have  # balans 0 dan pastga tushmasin
                    if _d == 0:
                        continue
                _db17.add(models.CoinEntry(
                    student_id=_sid, amount=_d, source="league",
                    note=_note17, created_by="Tizim"))
                _db17.commit()
                _fixed17 += 1
            _db17.commit()
            _sm17(_db17, "league_coin_rescale_v1")
except Exception:
    pass

# ---------------------------------------------------------------------
# TENGLASHTIRISH DUBLIKATINI TUZATISH (2026-08-20, kechqurun).
# Yuqoridagi bir martalik tenglashtirish ikkita lambda bir vaqtda
# uyg'onganida BA'ZI o'quvchilarga ikki marta yozilib qolgan (masalan
# -8 va yana -8). Bu biznes ma'lumoti emas - tizimning o'zi bir necha
# soniya ichida takror yozgan texnik dublikat, shuning uchun ortiqcha
# nusxasi olib tashlanadi (har o'quvchida bittasi qoladi).
try:
    from sqlalchemy.orm import Session as _VS18
    from common import _seed_done as _sd18, _seed_mark as _sm18
    with _VS18(engine) as _db18:
        if not _sd18(_db18, "league_coin_rescale_fix_v2"):
            _note18 = ("Liga coinlari yangi shkalaga tenglashtirildi "
                       "(2026-08-20 qoidasi)")
            _rows18 = (_db18.query(models.CoinEntry)
                       .filter(models.CoinEntry.note == _note18)
                       .order_by(models.CoinEntry.student_id,
                                 models.CoinEntry.id).all())
            _seen18 = set()
            for _e in _rows18:
                if _e.student_id in _seen18:
                    _db18.delete(_e)   # texnik dublikat
                else:
                    _seen18.add(_e.student_id)
            _db18.commit()
            _sm18(_db18, "league_coin_rescale_fix_v2")
except Exception:
    pass
