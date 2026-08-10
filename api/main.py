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
from common import _in_user_branches, _charge_from_activation, _charge_skipped, _check_enrolment, _check_teacher_load, _ensure_public_id, _ensure_teacher_card, _get_group_in_scope, _group_students, _hr_task_for, _lessons_left_in_month, _period_key, _raise_if_blocked, _student_discount_percent, _support_month, _sync_student_left_date, _teacher_of_user, _time_to_min, _utc_window, backfill_missing_ids, scope_to_branch, student_balance
from dashboard import _collection_bonus, _first_payment_dates, _new_client_bonus, _payment_first_dates, admin_kpi
from groups_lessons import _sync_scheduled_lessons
from inventory import _check_stock
from me import _my_teacher_or_404
from support import _days_uz, _support_conflicts
from timetable import require_perm
from common import _ensure_month_charges
from content import _period_range, _smm_kpi

Base.metadata.create_all(bind=engine)

from common import _schema_bootstrap  # noqa: E402

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
