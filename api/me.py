"""Auto-extracted from main.py during refactor (split-main). Domain: me."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request
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
from auth import is_partner_head as _is_partner_head
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

# me.py ichida boshqa domendagi route-funksiyalar to'g'ridan-to'g'ri
# (HTTP orqali emas, oddiy Python chaqiruvi sifatida) qayta ishlatiladi -
# main.py bo'linishidan oldin bitta fayl bo'lgani uchun bu ishlagan,
# endi aniq import kerak.
from teachers import teacher_career

router = APIRouter()


@router.get("/api/me/smm-salary")
def my_smm_salary(db: Session = Depends(get_db),
                  user=Depends(require_role(roles.SMM_MANAGER))):
    from salary_coach import own_smm_salary, student_plan_state
    return own_smm_salary(user, db, roles.local_today(), student_plan_state)

def _group_homework(db: Session, group_id: int,
                    since: date | None = None) -> dict:
    """Guruhning uy vazifasi foizi."""
    q = (db.query(models.Attendance, models.Lesson)
         .join(models.Lesson,
               models.Attendance.lesson_id == models.Lesson.id)
         .filter(models.Lesson.group_id == group_id,
                 models.Attendance.homework.isnot(None)))
    if since:
        q = q.filter(models.Lesson.date >= since)
    rows = q.all()
    done = sum(1 for a, _ in rows if a.homework == 1)
    n = len(rows)
    pct = round(done / n * 100, 1) if n else None
    label, tone = roles.homework_band(
        pct if n >= roles.HOMEWORK_MIN_CHECKED else None)
    return {"checked": n, "done": done, "percent": pct,
            "label": label, "tone": tone}

_VOLUNTEER_HINT = ("Siz hozir Volontyor bosqichidasiz - bu tajriba "
                   "to'plash davri, oylik hisoblanmaydi. Junior "
                   "darajaga o'tganingizda oyligingiz shu yerda "
                   "ko'rinadi.")


ENGLISH_SUBJECTS = ("english", "kids_english")


def is_english_teacher(db: Session, user) -> bool:
    """Dars rejalari faqat INGLIZ TILI ustozlariga (2026-09-18, Jahongir:
    "barcha ingliz til ustozlariga chiqsin boshqa ustozlarga chiqmasin").
    Ustoz/support bo'lmagan xodimlar uchun cheklov yo'q. Fani yozilmagan
    ustoz — inglizchi deb qabul qilinadi (yopib qo'ymaslik uchun).

    2026-09-18 (Jahongir: "Shirinabonu ko'rinmayabdi deyabdi"): fan
    maydoni "English"/"Ingliz tili"/"IELTS" kabi erkin yozilgan yoki
    noto'g'ri tanlangan bo'lsa ham, ustozga INGLIZ TILI GURUHI
    biriktirilgan bo'lsa — inglizchi. Faqat boshqa fan ustozi (fani
    aniq boshqa VA bironta ingliz guruhi yo'q) yopiladi."""
    if user.role not in (roles.TEACHER, roles.SUPPORT_TEACHER):
        return True
    t = _teacher_of_user(db, user)
    if not t:
        return True
    subj = (getattr(t, "subject", None) or "").strip().lower()
    if not subj:
        return True
    for x in subj.split(","):
        x = x.strip()
        if x in ENGLISH_SUBJECTS or "english" in x or "ingliz" in x                 or "ielts" in x:
            return True
    # Fani boshqa yozilgan, lekin ingliz tili guruhi bor — inglizchi.
    g = (db.query(models.Group.id)
         .filter(models.Group.teacher_id == t.id,
                 func.lower(models.Group.subject).in_(ENGLISH_SUBJECTS))
         .first())
    return g is not None


def _is_volunteer(db: Session, user) -> bool:
    """Volontyor darajadagi support/examinerga oylik KO'RINMAYDI.

    Jahongir: "Volunteer darajadagi support teacher oyligi umuman
    o'ziga korinmasin, chunki u oylik olmaydi, lekin hisobotda
    rahbariyatga korinsin. Examinerlarda ham Volunteer examiner
    darajasi bor ularda ham oylik ko'rinmasin".

    Rahbariyat hisobotlariga (Moliya -> Ish haqi) bu tegmaydi - u
    yerda volontyor 0 so'm bilan ko'rinib turadi. Daraja yozuvi
    bo'lmasa ham volontyor hisoblanadi (daraja qo'yilmagan yangi
    xodim) - bu payroll hisobi bilan bir xil qoida."""
    graded = (roles.SUPPORT_TEACHER, roles.EXAMINER,
              roles.HEAD_EXAMINER, roles.HEAD_SUPPORT)
    if user.role not in graded:
        return False
    SG = getattr(models, "StaffGrade", None)
    if SG is None:
        return False
    try:
        r = db.query(SG).filter(SG.user_id == user.id).first()
        return (r.grade if r and r.grade else "volunteer") == "volunteer"
    except Exception:
        return False


@router.get("/api/my/salary")
def my_salary(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_SELF_VIEW)),
):
    """Ustozning o'z oyligi. Kirgan zahoti shu kungacha ishlab topgan
    puli va balansi ko'rinadi."""
    if _is_volunteer(db, user):
        return {"volunteer": True, "hint": _VOLUNTEER_HINT}
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Sizga bog'langan ustoz yozuvi topilmadi")
    card = _salary_card(db, t)
    card["can_pay"] = False
    return card

@router.get("/api/my/finance")
def my_finance(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_SELF_VIEW)),
):
    """Ustozning MOLIYA bo'limi: oylar bo'yicha oylik tarixi —
    ishlab topgan, olgan, qoldiq, yig'ilib boruvchi balans
    (2026-09-05, Jahongir: "oyliklar tarixi bo'lsin")."""
    if _is_volunteer(db, user):
        return {"volunteer": True, "hint": _VOLUNTEER_HINT}
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Sizga bog'langan ustoz yozuvi topilmadi")
    out = _finance_ledger(db, t)
    out["can_pay"] = False
    return out

@router.get("/api/me/career")
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

# =====================================================================
#  XODIM TELEGRAMINI ULASH (2026-08-15)
#  Asoschiga kunlik zaxira fayli va server xatosi ogohlantirishi
#  Telegram orqali boradi — buning uchun chat bir marta bog'lanishi
#  kerak. Kod profilda ko'rinadi, xodim uni botga yozadi.
# =====================================================================
@router.get("/api/me/telegram")
def my_telegram(db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    import notify
    me = db.query(models.User).get(user.id)
    if me is None:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    if not me.tg_code:
        # Taxmin qilib bo'lmaydigan qisqa kod
        import secrets
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(6):
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            clash = (db.query(models.User)
                     .filter(models.User.tg_code == code).first()
                     or db.query(models.Student)
                     .filter(models.Student.tg_code == code).first())
            if not clash:
                me.tg_code = code
                db.commit()
                break
    bot = None
    try:
        bot = notify.bot_info()
    except Exception:
        bot = None
    return {
        "code": me.tg_code,
        "linked": bool(me.telegram_chat_id),
        "bot": bot,
        "bot_link": (f"https://t.me/{bot}?start={me.tg_code}"
                     if bot and me.tg_code else None),
        "ready": notify.enabled(),
    }


@router.delete("/api/me/telegram")
def unlink_telegram(db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    """Aloqani uzish — masalan telefon almashtirilganda."""
    me = db.query(models.User).get(user.id)
    if me:
        me.telegram_chat_id = None
        db.commit()
    return {"ok": True}


@router.get("/api/me")
def my_identity(db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Kim ekanini yengil qaytaradi. Frontend login paytida keshlagan
    ism/rolni har ochilishda shu yerdan yangilab oladi — ism serverda
    o'zgarsa (masalan Administrator -> Asoschi) burchakdagi profil
    chipida eskirib qolmasligi uchun.

    branches — xodim ishlaydigan BARCHA filiallar (asosiy + qo'shimcha).
    Ikkitadan ko'p bo'lsa, tepadagi filial tanlagich shu ro'yxatdan
    chiqadi (2026-08-10: ikki filialda dars beradigan ustozda tanlagich
    umuman chiqmasdi — u faqat butun tashkilotni ko'radiganlarga
    ko'rsatilardi)."""
    ids = _user_branch_ids(db, user)
    branches = []
    if ids:
        rows = (db.query(models.Branch)
                .filter(models.Branch.id.in_(ids))
                .order_by(models.Branch.name).all())
        branches = [{"id": b.id, "name": b.name} for b in rows]
    # KO'P LAVOZIM (2026-08-10): xodimda qo'shimcha lavozim bo'lsa,
    # tepadagi lavozim tanlagichi shu ro'yxatdan chiqadi.
    my_roles = _user_roles(db, user)
    return {
        "full_name": user.full_name,
        "role": user.role,
        "branch_id": user.branch_id,
        "role_label": roles.UZ_LABELS.get(user.role, user.role),
        "branches": branches,
        "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                  for r in my_roles],
        # Volontyor support/examiner - "Mening oyligim" umuman
        # ko'rinmasin (Jahongir)
        "salary_hidden": _is_volunteer(db, user),
        # Hamkor markaz (Stech) rahbari — o'z markazida asoschi kabi
        # (2026-09-17). Frontend shu bo'yicha tugmalarni ochadi.
        "partner_head": _is_partner_head(user),
        # Dars rejalari / jonli o'yin faqat ingliz tili ustozlariga
        "english_teacher": is_english_teacher(db, user),
        # Kuzatuvchi (2026-10-19): asoschi ekranlari, lekin faqat ko'rish
        "read_only": bool(getattr(user, "_observer", False)),
    }

@router.get("/api/me/permissions")
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

def _branch_label(db: Session, user, branch_id) -> str | None:
    """Kartalar qaysi filial bo'yicha ekani — bir qatorda.

    Yozuv RAQAMGA mos bo'lishi shart. Avval bu yerda doim xodimning
    o'z filiali yozilardi: tanlagichda "Zafar" turgan, sarlavhada
    esa "Maktab" — Jahongir aynan shuni ko'rgan.
    """
    if branch_id:
        b = db.query(models.Branch).get(branch_id)
        if b:
            return b.name
    # Filial tanlanmagan: raqamlar bir nechta filialdan yig'ilgan
    # bo'lsa, shuni ochiq aytamiz.
    try:
        from common import visible_branch_ids
        n = len(visible_branch_ids(db, user))
    except Exception:
        n = 1
    if n > 1:
        return "Barcha filiallar"
    return user.branch.name if user.branch else None


@router.get("/api/me/dashboard")
def my_dashboard(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Xodimning O'Z dashboardi. Har bir rol o'ziga tegishli raqamni
    ko'radi — birovning ishi uni chalg'itmaydi.

    2026-08-27, Jahongir: "hamma filiallni tanlasa, zafarni tanlasa
    ham shu chiqyabdi unga togri chiqarsin filiallar boyicha ham".

    Sabab shu yerda edi: endpoint filial parametrini UMUMAN qabul
    qilmasdi. Tepadagi tanlagich boshqa sahifalarni o'zgartirardi-yu,
    "Mening ishim" kartalari qotib turardi."""
    # AVTOMAT: tug'ilgan kun va yubiley eslatmalari. HR hisobiga kirgan
    # zahoti vazifa paydo bo'ladi — hech kim tugma bosmaydi.
    if user.role in roles.STAFF_DATES_ACCESS:
        try:
            _ensure_staff_date_tasks(db, user)
        except Exception:
            db.rollback()

    # Ketish xavfi skaneri - kuniga bir marta, kim birinchi kirsa
    try:
        _risk_scan(db)
    except Exception:
        db.rollback()

    builder = _MY_CARDS.get(user.role)
    cards = builder(db, user, branch_id) if builder else []

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
        # Sarlavhada TANLANGAN filial nomi turadi. Avval doim
        # xodimning o'z filiali chiqardi — tanlagichda "Zafar",
        # sarlavhada "Maktab" bo'lib chalkashtirardi.
        "branch": _branch_label(db, user, branch_id),
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
        # Ustoz uchun: davomat, riskdagi o'quvchilar, rivojlanish va
        # kritik ogohlantirishlar. Boshqa rollarda None.
        "teacher": (_safe_teacher_dashboard(db, user)
                    if user.role in tuple(roles.SELF_STATS) else None),
    }

def _safe_teacher_dashboard(db: Session, user: models.User):
    """Ustoz bloki xato bersa butun dashboard qulab tushmasin."""
    try:
        return _teacher_dashboard(db, user)
    except Exception:
        db.rollback()
        return None

@router.get("/api/me/profile")
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
        ctx = billing.PayrollContext(db)      # 2 hisob, 1 marta o'qish
        ctx.prefetch([t.id])
        e = _teacher_earned(db, t.id, since=m_start, until=m_end, ctx=ctx)
        paid_m = _teacher_paid(db, t.id, since=m_start, until=m_end, ctx=ctx,
                               period=period)
        balance = round(_teacher_earned(db, t.id, ctx=ctx)["amount"]
                        - _teacher_paid(db, t.id, ctx=ctx), 2)
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
            # entry.py buni almashtirishi mumkin (M.admin_kpi = ...,
            # "MyProfile ham shu hisobdan foydalanadi" izohiga qarang)
            # - main orqali dinamik chaqiramiz.
            import main as _main
            k = _main.admin_kpi(year=today.year, month=today.month, db=db, user=user)
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

def _held_coins(db: Session, student_id: int) -> int:
    """So'ralgan, lekin hali berilmagan sovg'alarga band qilingan coin."""
    rows = (db.query(models.RewardRedemption)
            .filter(models.RewardRedemption.student_id == student_id,
                    models.RewardRedemption.status == "requested").all())
    return sum(r.coins or 0 for r in rows)

def _reward_task_title(redemption_id: int) -> str:
    """Vazifa sarlavhasidagi barqaror belgi. Sovg'a berilganda shu
    matn bo'yicha vazifa topiladi va yopiladi."""
    return f"Sovg'a so'rovi #R{redemption_id}"


# Sovg'ani kim beradi — birinchi topilgani vazifani oladi. Tartib
# ataylab shunday: kundalik ish administratorda, u bo'lmasa support,
# eng oxirida rahbariyat bezovta qilinadi.
_REWARD_TASK_ROLES = [
    [roles.ADMINISTRATOR],
    [roles.HEAD_SUPPORT, roles.SUPPORT_TEACHER],
    [roles.ACADEMIC_HEAD, roles.SALES_MANAGER],
    [roles.BRANCH_MANAGER],
    [roles.FOUNDER],
]


def _reward_task_assignee(db: Session, branch_id):
    """Filialdagi eng mos xodim. Filialda topilmasa — umumiy."""
    for group in _REWARD_TASK_ROLES:
        q = db.query(models.User).filter(models.User.role.in_(group),
                                         models.User.is_active == 1)
        if branch_id:
            who = q.filter(models.User.branch_id == branch_id).first()
            if who:
                return who
    for group in _REWARD_TASK_ROLES:
        who = (db.query(models.User)
               .filter(models.User.role.in_(group),
                       models.User.is_active == 1).first())
        if who:
            return who
    return None


def _reward_request_task(db: Session, s, r, red) -> None:
    """O'quvchi sovg'a so'radi — xodimga vazifa."""
    title = _reward_task_title(red.id)
    if db.query(models.Task).filter(models.Task.title == title).first():
        return
    who = _reward_task_assignee(db, s.branch_id)
    body = (f"{s.full_name}"
            + (f" ({s.group.name})" if s.group else "")
            + f" — \"{r.name}\" sovg'asini {red.coins} coinga olmoqchi.\n\n"
              f"Coin band qilindi. Sovg'ani qo'lga bergach "
              f"Gamifikatsiya → Sovg'a so'rovlari bo'limida "
              f"\"Berildi\" tugmasini bosing — shundagina coin "
              f"hisobdan yechiladi. Rad etilsa coin qaytadi.")
    task = models.Task(
        title=title, description=body,
        assignee_id=who.id if who else None,
        branch_id=s.branch_id,
        deadline=date.today() + timedelta(days=2),
        priority="normal", source="manual", created_by="Jony Shop")
    db.add(task)
    db.flush()
    _ensure_public_id(db, "task", task)


def _reward_out(r: models.Reward, balance: int = None,
                pay_balance: float = None) -> dict:
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
        # COINGA CHEGIRMA (2026-08-15): sovg'adan farqli - qo'lga
        # berilmaydi, to'g'ridan-to'g'ri to'lovga tushadi.
        "kind": getattr(r, "kind", "gift") or "gift",
        "discount_percent": getattr(r, "discount_percent", None),
        "discount_amount": getattr(r, "discount_amount", None),
        # Do'kon kartasidagi rasm (2026-08-20)
        "image": getattr(r, "image", None),
        # Bugun sotib olinsa QAYSI OYGA tegishli bo'ladi
        # (2026-08-20: sanaga emas, BALANSGA qarab - qarzli bo'lsa
        # shu oyga, to'lagan bo'lsa keyingi oyga)
        "period": (roles.shop_discount_period_by_balance(pay_balance or 0)
                   if (getattr(r, "kind", "gift") or "gift") == "discount"
                   else None),
        # Coin yetsa DARROV beriladimi yoki xodim tasdig'i kerakmi
        # (2026-08-20). Ilova shu bayroqqa qarab to'g'ri yozuv
        # ko'rsatadi - o'quvchi nima bo'lishini oldindan biladi.
        "auto": roles.shop_auto_discount(r),
    }

@router.get("/api/me/coins")
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

    # PUL balansi - chegirma qaysi oyga tushishini aytish uchun
    # (2026-08-20, Jahongir qoidasi).
    _pay_bal = student_balance(db, s.id)

    return {
        "student_id": s.id,
        "full_name": s.full_name,
        "group": s.group.name if s.group else None,
        "balance": balance,
        "earned": earned,
        "spent": spent,
        "held": held,
        "available": available,
        "next_goal": (_reward_out(next_goal, available, _pay_bal)
                      if next_goal else None),
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
        "rewards": [_reward_out(r, available, _pay_bal) for r in rewards],
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

@router.post("/api/me/rewards/{reward_id}")
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

    # ---------------------------------------------------------------
    #  COINGA CHEGIRMA (2026-08-15, Jahongir: "Jony Shopda coiniga
    #  skidka sotib olsa avtomat balansida shu narsa ozgarsin va
    #  15-kungacha sotib olsa shu oy uchun 15-kundan keyin sotib olsa
    #  keyingi oyga ishlasin").
    #
    #  Sovg'adan farqi: buni QO'LGA BERISH kerak emas, shuning uchun
    #  ODAM ARALASHMAYDI - coin darrov yechiladi va chegirma o'z
    #  oyiga yoziladi.
    # ---------------------------------------------------------------
    # AVTOMAT FAQAT 33% VA 100% (2026-08-20, Jahongir: "33% lik va
    # 100% lik chegirmalarni o'quvchi shopdan sotib olganda coini
    # yetsa avtomat berilsin admin tasdiqlashi shartmas, qolganlarini
    # admin tasdiqlashi va berishi kerak bo'ladi"). Qolgan chegirmalar
    # ham sovg'a kabi so'rov bo'lib xodimga tushadi - chegirmaning
    # o'zi tasdiqlanganda yaratiladi (gamification.give_reward).
    if roles.shop_auto_discount(r):
        # QAYSI OYGA (2026-08-20, Jahongir: "osha olgan oyiga
        # tolamagan bolsa shu olgan oyiga balans ozgarsin, agar
        # tolagan bolsa keyingi oyga"). Oybek misolida: -158 000
        # qarzli edi, 20-avgustda oldi - eski 15-kun qoidasi
        # sentabrga yozib yubordi va "balans o'zgarmadi" bo'ldi.
        period = roles.shop_discount_period_by_balance(
            student_balance(db, s.id))
        y, m = int(period[:4]), int(period[5:7])
        first = date(y, m, 1)
        last = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)

        red = models.RewardRedemption(
            student_id=s.id, reward_id=r.id, coins=r.cost,
            status="given", requested_by_student=1,
            given_by="Jony Shop (avtomat)", given_at=datetime.utcnow(),
            note=f"{period} oyiga chegirma", created_by=user.full_name)
        db.add(red)
        db.add(models.CoinEntry(
            student_id=s.id, amount=-abs(r.cost), source="reward",
            note=f"Jony Shop: {r.name} ({period} oyiga chegirma)",
            created_by="Jony Shop"))
        d = models.Discount(
            student_id=s.id, kind="coin_shop",
            percent=r.discount_percent, amount=r.discount_amount,
            reason=f"Jony Shop: {r.name} ({r.cost} coin)",
            start_date=first, end_date=last, status="active",
            period=period, requested_by=user.full_name,
            approved_by="Jony Shop (avtomat)",
            approved_at=datetime.utcnow())
        db.add(d)
        if r.stock is not None:
            r.stock = max(0, (r.stock or 0) - 1)
        db.commit()
        db.refresh(d)
        # Shu oyning hisobi allaqachon bo'lsa - balans DARROV o'zgaradi
        applied = 0
        try:
            applied = _apply_shop_discounts(db, period)
        except Exception:
            db.rollback()
        summa = _shop_discount_sum(db, s, d)
        when = ("shu oy" if period == roles.local_today().strftime("%Y-%m")
                else "keyingi oy (bu oy to'lab bo'lingan)")
        return {
            "id": red.id,
            "status": "given",
            "kind": "discount",
            "period": period,
            "amount": summa,
            "applied": bool(applied),
            "message": (
                f"Tabriklaymiz! \"{r.name}\" olindi. "
                + (f"{int(summa):,} so'm".replace(",", " ")
                   if summa else "Chegirma")
                + f" {when} ({period}) to'loviga hisoblanadi."
                + ("" if applied else
                   " Shu oy hisobi chiqishi bilan balansingizda "
                   "ko'rinadi.")),
            "available": available - r.cost,
        }

    red = models.RewardRedemption(
        student_id=s.id, reward_id=r.id, coins=r.cost,
        status="requested", requested_by_student=1,
        created_by=user.full_name)
    db.add(red); db.commit(); db.refresh(red)

    # -----------------------------------------------------------------
    #  ADMINGA VAZIFA (2026-08-16, Jahongir: "sovga yutib olsa
    #  adminlarga vazifa bolib borsin falonchi coinga shu narsa
    #  olmoqchi deb").
    #
    #  Sovg'a QO'LGA beriladi, ya'ni odam kerak. Ilova ichida
    #  bosilgan tugma xodimga yetib bormasa - o'quvchi kutib
    #  qoladi va coin band bo'lib turaveradi. Shuning uchun har
    #  so'rov Vazifalar bo'limiga tushadi.
    #
    #  Sarlavhada "#R<id>" turadi: sovg'a berilganda yoki rad
    #  etilganda aynan shu vazifa topilib yopiladi.
    # -----------------------------------------------------------------
    try:
        _reward_request_task(db, s, r, red)
        db.commit()
    except Exception:
        db.rollback()   # vazifa yaratilmasa ham so'rov saqlanib qoladi

    return {
        "id": red.id,
        "status": "requested",
        "message": (f"\"{r.name}\" so'raldi. {r.cost} coin band qilindi — "
                    f"administrator tasdiqlagach sovg'ani markazdan "
                    f"olib ketasiz."),
        "available": available - r.cost,
    }

@router.delete("/api/me/rewards/{redemption_id}")
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

@router.get("/api/me/gamification")
def my_gamification(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(404, "Sizning o'quvchi kartangiz topilmadi")
    return _student_gamification(db, s)

def _teacher_student_stats(db: Session) -> dict:
    """Har bir ustoz bo'yicha o'quvchi ko'rsatkichlari. Bir marta
    hisoblanadi, ham ustozning o'ziga, ham o'rtachaga ishlatiladi."""
    today = date.today()
    groups = {g.id: g for g in db.query(models.Group).all()}
    out: dict = {}

    for s in db.query(models.Student).all():
        g = groups.get(s.group_id)
        tid = g.teacher_id if g else None
        if tid is None:
            continue
        row = out.setdefault(tid, {
            "active": 0, "left": 0, "months": [], "left_students": [],
        })
        if s.left_date:
            row["left"] += 1
            row["months"].append(
                _months_between(s.enrolled_date or s.left_date, s.left_date))
            row["left_students"].append(s)
        elif s.status == "active":
            row["active"] += 1

    for tid, r in out.items():
        base = r["left"] + r["active"]
        r["total"] = base
        r["churn"] = round(r["left"] / base * 100, 1) if base else 0.0
        r["retention"] = round(100 - r["churn"], 1) if base else 0.0
        r["avg_months"] = (round(sum(r["months"]) / len(r["months"]), 1)
                           if r["months"] else None)
    return out

def _rank_of(value, others, higher_is_better=True):
    """Nechanchi o'rin. Qiymati yo'qlar hisobga olinmaydi."""
    vals = [v for v in others if v is not None]
    if value is None or len(vals) < roles.MIN_PEERS_FOR_RANK:
        return None, len(vals)
    better = sum(1 for v in vals
                 if (v > value if higher_is_better else v < value))
    return better + 1, len(vals)

@router.get("/api/me/results")
def my_results(db: Session = Depends(get_db),
               user=Depends(require_role(*roles.SELF_STATS))):
    """Ustozning o'z natijalari: qolganlar, ketganlar, o'rtacha muddat
    va markaz o'rtachasi bilan solishtirish."""
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(
            404, "Sizning ustoz yozuvingiz topilmadi. HR bilan "
                 "bog'laning — akkaunt ustoz kartasiga ulanmagan.")

    today = date.today()
    stats = _teacher_student_stats(db)
    mine = stats.get(t.id, {"active": 0, "left": 0, "total": 0,
                            "churn": 0.0, "retention": 0.0,
                            "avg_months": None, "left_students": []})

    # --- Markaz o'rtachasi (o'zidan tashqari) ---
    peers = {k: v for k, v in stats.items()
             if k != t.id and v["total"] >= roles.MIN_STUDENTS_FOR_STATS}
    churn_vals = [v["churn"] for v in peers.values()]
    month_vals = [v["avg_months"] for v in peers.values()
                  if v["avg_months"] is not None]
    avg_churn = round(sum(churn_vals) / len(churn_vals), 1) \
        if churn_vals else None
    avg_months = round(sum(month_vals) / len(month_vals), 1) \
        if month_vals else None

    enough = mine["total"] >= roles.MIN_STUDENTS_FOR_STATS
    # Ketish kam bo'lgani yaxshi
    churn_txt, churn_tone, churn_diff = roles.compare_verdict(
        mine["churn"] if enough else None, avg_churn, lower_is_better=True)
    ltv_txt, ltv_tone, ltv_diff = roles.compare_verdict(
        mine["avg_months"] if enough else None, avg_months)

    all_churn = [v["churn"] for v in stats.values()
                 if v["total"] >= roles.MIN_STUDENTS_FOR_STATS]
    all_months = [v["avg_months"] for v in stats.values()
                  if v["avg_months"] is not None
                  and v["total"] >= roles.MIN_STUDENTS_FOR_STATS]
    churn_rank, churn_peers = _rank_of(
        mine["churn"] if enough else None, all_churn,
        higher_is_better=False)
    ltv_rank, ltv_peers = _rank_of(
        mine["avg_months"] if enough else None, all_months)

    # --- Ketganlar ro'yxati, oynalar bo'yicha ---
    reasons = {r.student_id: r for r in db.query(models.LeaveReason).all()}
    groups = {g.id: g for g in db.query(models.Group).all()}
    month_start = today.replace(day=1)

    def leaver_row(s):
        r = reasons.get(s.id)
        key = r.reason if r else None
        g = groups.get(s.group_id)
        return {
            "id": s.id, "name": s.full_name,
            "group": g.name if g else None,
            "left_date": s.left_date.isoformat(),
            "enrolled_date": (s.enrolled_date.isoformat()
                              if s.enrolled_date else None),
            "months": round(_months_between(
                s.enrolled_date or s.left_date, s.left_date), 1),
            "reason": key,
            "reason_label": (roles.LEAVE_REASON_LABELS.get(key)
                             if key else "Sabab yozilmagan"),
            "controllable": key in roles.CONTROLLABLE_REASONS if key else None,
            "note": r.note if r else None,
        }

    all_left = sorted(mine.get("left_students", []),
                      key=lambda s: s.left_date, reverse=True)
    windows = []
    for key, label, days in roles.LEAVER_WINDOWS:
        since = month_start if days == 0 else today - timedelta(days=days)
        rows = [leaver_row(s) for s in all_left if s.left_date >= since]
        ctrl = sum(1 for r in rows if r["controllable"])
        windows.append({
            "key": key, "label": label,
            "since": since.isoformat(),
            "count": len(rows),
            "controllable": ctrl,
            "not_controllable": sum(1 for r in rows
                                    if r["controllable"] is False),
            "unknown": sum(1 for r in rows if r["controllable"] is None),
            "rows": rows[:60],
        })

    # Sabablar kesimi — oxirgi 1 yil
    year_rows = [leaver_row(s) for s in all_left
                 if s.left_date >= today - timedelta(days=365)]
    by_reason: dict = {}
    for r in year_rows:
        k = r["reason"] or "unknown"
        e = by_reason.setdefault(k, {
            "key": k, "label": r["reason_label"],
            "controllable": r["controllable"], "count": 0,
        })
        e["count"] += 1
    reason_rows = sorted(by_reason.values(), key=lambda r: -r["count"])

    hint = ("Ketish sabablarining hammasi ustozga bog'liq emas — "
            "ko'chib ketish yoki oilaviy sabab boshqa gap. Shuning "
            "uchun ro'yxat \"bizga bog'liq\" va \"bog'liq emas\" deb "
            "ajratilgan.")
    if not enough:
        hint = (f"Solishtirish uchun kamida "
                f"{roles.MIN_STUDENTS_FOR_STATS} ta o'quvchi kerak. "
                f"Sizda hozir {mine['total']} ta — raqamlar chiqadi, "
                f"lekin o'rtacha bilan solishtirish ishonchli emas.")

    return {
        "teacher": {"id": t.id, "name": t.full_name,
                    "grade": t.grade,
                    "grade_label": roles.GRADE_LABELS.get(t.grade or "", "—")},
        "students": {
            "active": mine["active"],
            "left": mine["left"],
            "total": mine["total"],
        },
        "retention": {
            "value": mine["retention"],
            "centre_avg": (round(100 - avg_churn, 1)
                           if avg_churn is not None else None),
        },
        "churn": {
            "value": mine["churn"],
            "centre_avg": avg_churn,
            "verdict": churn_txt, "tone": churn_tone, "diff": churn_diff,
            "rank": churn_rank, "peers": churn_peers,
        },
        "ltv": {
            "value": mine["avg_months"],
            "centre_avg": avg_months,
            "verdict": ltv_txt, "tone": ltv_tone, "diff": ltv_diff,
            "rank": ltv_rank, "peers": ltv_peers,
            "note": ("O'quvchi o'rtacha necha oy o'qigani. Faqat "
                     "ketganlar bo'yicha — hali o'qiyotganlar bu "
                     "raqamni sun'iy pasaytirmaydi."),
        },
        "windows": windows,
        "reasons": reason_rows,
        "enough_data": enough,
        "min_students": roles.MIN_STUDENTS_FOR_STATS,
        "hint": hint,
    }

def _my_teacher_or_404(db: Session, user) -> models.Teacher:
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(
            404, "Sizning ustoz yozuvingiz topilmadi. HR bilan "
                 "bog'laning — akkaunt ustoz kartasiga ulanmagan.")
    return t

@router.get("/api/me/groups")
def my_groups(db: Session = Depends(get_db),
              user=Depends(require_role(*roles.SELF_STATS))):
    """Faqat shu ustozning guruhlari."""
    t = _my_teacher_or_404(db, user)
    groups = _cabinet_groups(db, user, t)
    today = date.today()

    # =================================================================
    #  SUPPORT SOATI — MENEJER BIRIKTIRGANI (2026-09-10)
    # =================================================================
    #  Jahongir: "Supportlarga asosiy dars vaqti korinyabdi men
    #  belgilagan support soati emas, yani o'zlari otadigan soat emas,
    #  Birinchi ikkinchi guruh bir vaqtdrk koʻrinyabdi aslida bittasi
    #  2dan avval 2dan keyin ikkinchisi" va "support darslarni menejer
    #  biriktirgan shundan tortvol malumot".
    #
    #  Sabab: karta g.lesson_days / g.lesson_time — GURUHNING asosiy
    #  dars vaqtini ko'rsatardi. Support darsi esa alohida vaqtda
    #  o'tadi va u SupportAssignment (days/start/end) da turadi —
    #  aynan support menejer biriktirganda tanlagan kun va soat.
    #  Shuning uchun ikkala guruh bir xil "14:00" bo'lib chiqardi:
    #  ko'rsatilayotgani supportniki emas, guruhnikiydi.
    #
    #  Endi support uchun vaqt FAQAT biriktiruvdan olinadi. Biriktiruvda
    #  vaqt qo'yilmagan bo'lsa — guruh vaqtiga "tushib ketmaydi"
    #  (o'sha eski chalkashlik qaytardi), balki ochiq aytiladi.
    #
    #  2026-09-10 (ikkinchi bosqich): qoida common.py ga ko'chirildi —
    #  Jony Teacher ilovasi ham xuddi shu manbadan o'qiydi, aks holda
    #  bitta ekran tuzalib, ikkinchisi eskicha qolib ketardi.
    sup_slot = support_slot_map(db, user)

    rooms = {r.id: r.name for r in db.query(models.Room).all()}
    out = []
    for g in groups:
        students = [s for s in g.students if s.status == "active"]
        # Oxirgi va keyingi dars
        last = (db.query(models.Lesson)
                .filter(models.Lesson.group_id == g.id,
                        models.Lesson.held == 1,
                        models.Lesson.date <= today)
                .order_by(models.Lesson.date.desc()).first())
        nxt = (db.query(models.Lesson)
               .filter(models.Lesson.group_id == g.id,
                       models.Lesson.date > today)
               .order_by(models.Lesson.date).first())
        g_days, g_time, t_src, time_note = group_time_for(sup_slot, g)
        out.append({
            "id": g.id, "public_id": g.public_id, "name": g.name,
            "subject": g.subject,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "",
                                                      g.subject),
            "level": getattr(g, "level", None),
            "days": g_days, "time": g_time,
            # Support uchun ko'rsatilgan vaqt GURUHNIKI emas, o'ziniki
            "time_source": t_src,
            "time_note": time_note,
            "room": rooms.get(g.room_id) or g.room,
            "students": len(students),
            "started_on": (g.start_date.isoformat()
                           if g.start_date else None),
            "last_lesson": last.date.isoformat() if last else None,
            "next_lesson": nxt.date.isoformat() if nxt else None,
            "homework": _group_homework(
                db, g.id, since=today - timedelta(days=60)),
        })
    return {
        "rows": out,
        "total_groups": len(out),
        "total_students": sum(r["students"] for r in out),
        "hint": ("Guruh ustiga bosing — davomat, baholash va "
                 "imtihonlar ochiladi. Boshqa ustozlarning guruhlari "
                 "bu yerda ham, manzil qatoridan ham ochilmaydi."),
    }

@router.put("/api/me/groups/{group_id}")
def update_my_group(group_id: int, payload: schemas.MyGroupEdit,
                    force: bool = False,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.SELF_STATS))):
    """USTOZ O'Z GURUHINI TAHRIRLAYDI — faqat 4 ta maydon.

    2026-09-01, Jahongir: "ustozlar o'zlarini guruhlarini edit
    qilishda guruh nomini o'zgartirish darajasini va vaqtini
    o'zgartirish xonasini ozgartirish huquqi bolsin".

    Ruxsat: nom, daraja, dars vaqti, xona. Boshqa hech nima —
    narx, ustoz stavkasi, ustozning o'zi, filial, dars kunlari,
    boshlanish sanasi — bu yerdan o'zgarmaydi (schemas.MyGroupEdit
    ularni umuman qabul qilmaydi).

    Guruh BOSHQA ustozniki bo'lsa 403. Support ustoz biriktirilgan
    guruhini ham tahrirlay olmaydi — u guruhning egasi emas.

    Vaqt yoki xona o'zgarsa jadval to'qnashuvi tekshiriladi.
    Xona bandligi va ustozning ikki joyda bo'lishi "block" —
    ustoz uni force bilan ham aylanib o'tolmaydi. Faqat
    ogohlantirishlar (masalan darslar orasidagi bo'shliq)
    tasdiqlansa o'tadi.

    Har bir o'zgarish AUDITga yoziladi: rahbariyat kim guruh nomini
    yoki vaqtini o'zgartirganini ko'rib turadi."""
    t = _my_teacher_or_404(db, user)
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    if group.teacher_id != t.id:
        raise HTTPException(
            403, "Bu guruh sizniki emas — faqat o'zingizning "
                 "guruhingizni tahrirlay olasiz.")

    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "O'zgartirish uchun hech nima "
                                 "yuborilmadi")

    # --- Nom ---------------------------------------------------------
    if "name" in fields:
        name = (fields["name"] or "").strip()
        if not name:
            raise HTTPException(400, "Guruh nomi bo'sh bo'lmasin")
        if len(name) > 120:
            raise HTTPException(400, "Guruh nomi juda uzun (120 belgi)")
        fields["name"] = name

    # --- Daraja ------------------------------------------------------
    if "level" in fields:
        lvl = (fields["level"] or "").strip() or None
        if lvl and not roles.level_valid(group.subject, lvl):
            raise HTTPException(
                400, "Bu daraja guruhning faniga tegishli emas")
        fields["level"] = lvl

    # --- Dars vaqti --------------------------------------------------
    if "lesson_time" in fields:
        tm = (fields["lesson_time"] or "").strip() or None
        if tm:
            start, _end = _group_slot(
                type("T", (), {"lesson_time": tm})())
            if not start:
                raise HTTPException(
                    400, "Dars vaqti noto'g'ri. Namuna: 09:00")
        fields["lesson_time"] = tm

    # --- Xona --------------------------------------------------------
    if "room_id" in fields and fields["room_id"]:
        room = db.query(models.Room).get(fields["room_id"])
        if not room:
            raise HTTPException(400, "Bunday xona yo'q")
        # Xona BOSHQA filialniki bo'lmasin — ustoz o'z filialidagi
        # xonalardan tanlaydi.
        if (room.branch_id and group.branch_id
                and room.branch_id != group.branch_id):
            raise HTTPException(
                400, "Bu xona boshqa filialga tegishli")

    # Vaqt yoki xona tegilsa — jadval to'qnashuvi
    if "lesson_time" in fields or "room_id" in fields:
        _raise_if_blocked(
            _check_schedule(
                db, group_id=group.id, teacher_id=group.teacher_id,
                room_id=fields.get("room_id", group.room_id),
                lesson_days=group.lesson_days,
                lesson_time=fields.get("lesson_time", group.lesson_time)),
            force=force)

    audit.log_changes(db, user, entity="group", obj=group,
                      changes=fields, label_attr="name",
                      note="Ustoz o'z guruhini tahrirladi")
    for k, v in fields.items():
        setattr(group, k, v)
    # Eski matnli "room" maydoni yangi xona bilan mos qolsin — aks
    # holda ba'zi ro'yxatlarda eski xona nomi ko'rinib turadi.
    if "room_id" in fields:
        r = (db.query(models.Room).get(fields["room_id"])
             if fields["room_id"] else None)
        group.room = r.name if r else None
    db.commit()
    db.refresh(group)
    rooms = {r.id: r.name for r in db.query(models.Room).all()}
    return {
        "ok": True,
        "id": group.id,
        "name": group.name,
        "level": group.level,
        "lesson_time": group.lesson_time,
        "room_id": group.room_id,
        "room": rooms.get(group.room_id) or group.room,
    }


@router.get("/api/me/groups/{group_id}/edit-options")
def my_group_edit_options(group_id: int,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.SELF_STATS))):
    """Tahrir oynasi uchun tayyor ro'yxatlar: guruh fanidagi
    darajalar, dars vaqtlari va SHU FILIALdagi xonalar.

    Ustozga /api/rooms ochiq bo'lsa ham, bu yerda ro'yxat guruhning
    filialiga qarab kesiladi va bitta so'rovda keladi."""
    t = _my_teacher_or_404(db, user)
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    if group.teacher_id != t.id:
        raise HTTPException(403, "Bu guruh sizniki emas")

    rq = db.query(models.Room)
    if group.branch_id:
        rq = rq.filter(or_(models.Room.branch_id == group.branch_id,
                           models.Room.branch_id.is_(None)))
    rooms = [{"id": r.id, "name": r.name, "capacity": r.capacity}
             for r in rq.order_by(models.Room.name).all()]
    return {
        "subject": group.subject,
        "subject_label": roles.SUBJECT_LABELS.get(group.subject or "",
                                                  group.subject),
        "levels": [{"key": k, "label": lbl} for k, lbl
                   in roles.SUBJECT_LEVELS.get(group.subject or "", [])],
        "lesson_times": [
            {"start": x, "label": roles.lesson_time_range(x)}
            for x in roles.LESSON_START_TIMES],
        "rooms": rooms,
        "current": {
            "name": group.name, "level": group.level,
            "lesson_time": group.lesson_time, "room_id": group.room_id,
        },
        "hint": ("Faqat nom, daraja, dars vaqti va xona "
                 "o'zgartiriladi. Narx, ustoz va filial rahbariyatda "
                 "qoladi."),
    }


@router.get("/api/me/students")
def my_students(group_id: int | None = None, q: str | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SELF_STATS))):
    """Ustozning o'z o'quvchilari — akademik ko'rsatkichlar bilan.

    BALANS QAYTARILMAYDI. Bu ataylab: ustoz bolaga qarzdorligi orqali
    emas, o'qishi orqali qarashi kerak."""
    t = _my_teacher_or_404(db, user)
    groups = _cabinet_groups(db, user, t)
    gid_map = {g.id: g for g in groups}
    if group_id and group_id not in gid_map:
        raise HTTPException(403, "Bu guruh sizniki emas")

    query = db.query(models.Student).filter(
        models.Student.group_id.in_(list(gid_map.keys()) or [-1]))
    # MUZLATILGAN O'QUVCHI USTOZGA KO'RINADI (2026-09-03, Jahongir:
    # "ustozlarga muzlatilgan o'quvchilari korinsin faqat yoqlamasi
    # chiqmasin").
    #
    # 2026-08-10 da qoida boshqacha edi ("muzlatilgan o'quvchilar
    # o'qituvchilarga ko'rinmasin") va ular ro'yxatdan butunlay
    # olib tashlangan edi. Lekin shunda ustoz bolaning qayerga
    # yo'qolganini bilmay qolardi. Endi ular RO'YXATDA turadi va
    # "Muzlatilgan" deb belgilanadi — ustoz kimlar qaytishini
    # ko'rib turadi.
    #
    # ASOSIY QOIDA O'ZGARMADI: yo'qlama — ish haqi hujjati, shuning
    # uchun muzlatilgan o'quvchi DAVOMAT JADVALIGA umuman
    # tushmaydi va unga yo'qlama ham, baho ham qo'yib bo'lmaydi
    # (entry.py dagi "MUZLATILGAN O'QUVCHI YO'QLAMADA HECH KIMGA
    # KO'RINMASIN" bloki — u yerga tegilmadi).
    if group_id:
        query = query.filter(models.Student.group_id == group_id)
    if q:
        query = query.filter(models.Student.full_name.ilike(f"%{q}%"))
    students = query.order_by(models.Student.full_name).all()
    if not students:
        return {"rows": [], "groups": [{"id": g.id, "name": g.name}
                                       for g in groups],
                "total": 0, "hint": _my_students_hint()}

    sids = [s.id for s in students]
    since = date.today() - timedelta(days=90)

    # Davomat — oxirgi 3 oy
    att_rows = (db.query(models.Attendance, models.Lesson)
                .join(models.Lesson,
                      models.Attendance.lesson_id == models.Lesson.id)
                .filter(models.Attendance.student_id.in_(sids),
                        models.Lesson.date >= since).all())
    att: dict = {}
    for a, ls in att_rows:
        e = att.setdefault(a.student_id, {"total": 0, "present": 0})
        e["total"] += 1
        if a.present:
            e["present"] += 1

    # Kunlik baholar
    gr_rows = db.query(models.DailyGrade).filter(
        models.DailyGrade.student_id.in_(sids)).all()
    grades: dict = {}
    for g in gr_rows:
        if g.score is not None:
            grades.setdefault(g.student_id, []).append(g.score)

    # Imtihon natijalari
    ex_rows = db.query(models.ExamResult).filter(
        models.ExamResult.student_id.in_(sids)).all()
    exams: dict = {}
    for e in ex_rows:
        if e.band is not None:
            exams.setdefault(e.student_id, []).append(e.band)

    # Coin va XP — rag'batlantirish uchun
    gam = {g.student_id: g for g in db.query(models.StudentGamification)
           .filter(models.StudentGamification.student_id.in_(sids)).all()}

    rows = []
    for s in students:
        a = att.get(s.id, {"total": 0, "present": 0})
        pct = (round(a["present"] / a["total"] * 100, 1)
               if a["total"] else None)
        gl = grades.get(s.id, [])
        el = exams.get(s.id, [])
        g = gid_map.get(s.group_id)
        gm = gam.get(s.id)
        hw = _homework_stats(db, s.id)
        rows.append({
            "id": s.id, "public_id": s.public_id, "full_name": s.full_name,
            "group_id": s.group_id, "group": g.name if g else None,
            "status": s.status,
            "enrolled_date": (s.enrolled_date.isoformat()
                              if s.enrolled_date else None),
            "months": (round(_months_between(s.enrolled_date, date.today()), 1)
                       if s.enrolled_date else None),
            # ---- Akademik ko'rsatkichlar ----
            "attendance_percent": pct,
            "lessons_counted": a["total"],
            "missed": a["total"] - a["present"],
            "avg_grade": round(sum(gl) / len(gl), 1) if gl else None,
            "grades_count": len(gl),
            "last_exam": el[-1] if el else None,
            "best_exam": max(el) if el else None,
            "xp": round(gm.lifetime_xp or 0, 1) if gm else 0,
            "level": gm.current_level if gm else 1,
            # ---- Uy vazifasi ----
            "homework_percent": hw["percent"],
            "homework_checked": hw["checked"],
            "homework_label": hw["label"],
            "homework_tone": hw["tone"],
            "homework_low": (hw["enough"] and hw["percent"] is not None
                             and hw["percent"] < roles.HOMEWORK_RISK_PERCENT),
            # Davomat past bo'lsa ustoz ko'rsin
            "at_risk": pct is not None and pct < 70 and a["total"] >= 4,
        })
    return {
        "rows": rows,
        "groups": [{"id": g.id, "name": g.name} for g in groups],
        "total": len(rows),
        "at_risk": sum(1 for r in rows if r["at_risk"]),
        "homework_low": sum(1 for r in rows if r["homework_low"]),
        "homework_threshold": roles.HOMEWORK_RISK_PERCENT,
        # Muzlatilganlar soni — ekranda alohida eslatma chiqadi
        "frozen": sum(1 for r in rows if r["status"] == "frozen"),
        "hint": _my_students_hint(),
    }

def _my_students_hint() -> str:
    return ("Faqat sizning o'quvchilaringiz. To'lov va balans "
            "ko'rsatilmaydi — bu administrator va moliya bo'limining "
            "ishi. Muzlatilganlar ro'yxatda turadi, lekin davomat "
            "jadvaliga tushmaydi — ularga yo'qlama qo'yilmaydi.")


@router.post("/api/me/students/{student_id}/coin-deduct")
def my_student_coin_deduct(student_id: int, payload: schemas.CoinManual,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(roles.TEACHER))):
    """Ustoz o'z o'quvchisidan intizom uchun coin AYIRADI.

    Jahongir (2026-08-12): "ustozlarga coin ayrish imkonini berish
    funksiyasini qoshib qoy, minimum 1ta maksimum 15ta gacha ayrish
    mumkin". Faqat ayirish — coin BERISH avvalgidek kunlik baho,
    imtihon va rahbariyat (Gamification) orqali qoladi, aks holda
    ustozlar coin tarqatib inflyatsiya bo'lardi.
    """
    try:
        amount = int(payload.amount)
    except Exception:
        raise HTTPException(400, "Miqdor noto'g'ri")
    if amount < 1 or amount > 15:
        raise HTTPException(400, "1 tadan 15 tagacha ayirish mumkin")

    t = _my_teacher_or_404(db, user)
    gids = {g.id for g in _cabinet_groups(db, user, t)}
    s = db.query(models.Student).get(student_id)
    if not s or s.group_id not in gids:
        raise HTTPException(403, "Bu o'quvchi sizning guruhingizda emas")
    if s.status == "frozen":
        raise HTTPException(400, "Muzlatilgan o'quvchidan coin ayirilmaydi")

    note = (payload.note or "").strip()
    db.add(models.CoinEntry(
        student_id=s.id, amount=-amount, source="teacher_deduct",
        note=note or None, created_by=user.full_name))
    db.commit()
    audit.log(db, user, entity="student", action="coin_deduct",
              entity_id=s.id, entity_label=s.full_name,
              new_value=-amount, note=note or None,
              branch_id=s.branch_id, commit=True)
    return {"ok": True, "amount": -amount,
            "balance": _student_coin_balance(db, s.id)}

@router.get("/api/me/reschedules")
def my_reschedules(db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.SELF_STATS))):
    """Kvota va surish tarixi."""
    t = _my_teacher_or_404(db, user)
    today = date.today()
    nxt = _month_end(today) + timedelta(days=1)
    quota = _reschedule_usage(db, t.id, today)
    # Kelasi oy ham ko'rsatiladi: kvota DARS oyi bo'yicha sanaladi,
    # shuning uchun oy oxirida ustoz "menda 2 ta bor" deb o'ylab
    # adashmasin
    quota_next = _reschedule_usage(db, t.id, nxt)
    rows = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.teacher_id == t.id).order_by(
        models.LessonReschedule.id.desc()).limit(60).all()
    return {
        "quota": quota,
        "quota_next": quota_next,
        "next_month": nxt.isoformat(),
        "rows": [_resch_out(db, r) for r in rows],
        "reasons": [{"key": k, "label": l}
                    for k, l in roles.RESCHEDULE_REASONS],
        "min_notice_days": roles.RESCHEDULE_MIN_NOTICE_DAYS,
        "max_shift_days": roles.RESCHEDULE_MAX_SHIFT_DAYS,
        "carry_over": roles.RESCHEDULE_CARRY_OVER,
        # 2026-09-24: ustozda avtomat surish o'chirildi, shuning
        # uchun matn ham o'zgardi (roles.RESCHEDULE_TEACHER_AUTO).
        "hint": ("Har bir dars ko'chirish o'quv bo'limi tasdig'idan "
                 "o'tadi. So'rovingiz tasdiqlanmaguncha dars eski "
                 "kunida qoladi — o'quvchilarni oldindan "
                 "ogohlantirmang. Dars ko'p surilsa o'quvchining "
                 "qiziqishi tushadi."
                 if not roles.RESCHEDULE_TEACHER_AUTO else
                 f"Oyiga {roles.RESCHEDULE_PER_MONTH} marta avtomat "
                 f"ruxsat beriladi, 6 oyda jami "
                 f"{roles.RESCHEDULE_PER_WINDOW} marta. Foydalanilmagan "
                 f"imkon keyingi oyga o'tmaydi. Dars ko'p surilsa "
                 f"o'quvchining qiziqishi tushadi — shuning uchun "
                 f"chegara bor. Kvota DARS qaysi oyda bo'lsa, o'sha "
                 f"oyga yoziladi."),
        "cannot_cancel": ("Darsni bekor qilish mumkin emas — faqat "
                          "boshqa kunga ko'chiriladi."),
    }

@router.post("/api/me/reschedules")
def my_reschedule_add(payload: schemas.RescheduleIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SELF_STATS))):
    t = _my_teacher_or_404(db, user)
    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if g.teacher_id != t.id:
        raise HTTPException(403, "Bu guruh sizniki emas")

    today = roles.local_today()
    # O'tmishga surib bo'lmaydi — bu "bekor qilish"ning yashirin
    # yo'li bo'lib qolmasin. BUGUNGA surish mumkin (Jahongir,
    # 2026-08-11: "kelajakdagi darsni bugunga sura olmayabdi").
    if payload.to_date < today:
        raise HTTPException(400, "O'tib ketgan sanaga surib bo'lmaydi")
    if payload.to_date == payload.from_date:
        raise HTTPException(400, "Yangi sana eskisidan farq qilishi kerak")
    if payload.from_date < today:
        raise HTTPException(400, "O'tib ketgan darsni ko'chirib bo'lmaydi")

    notice = (payload.from_date - today).days
    if notice < roles.RESCHEDULE_MIN_NOTICE_DAYS:
        raise HTTPException(
            400, f"Kamida {roles.RESCHEDULE_MIN_NOTICE_DAYS} kun oldin "
                 f"so'ralishi kerak — o'quvchi va ota-onani "
                 f"ogohlantirishga vaqt kerak")
    shift = abs((payload.to_date - payload.from_date).days)
    if shift > roles.RESCHEDULE_MAX_SHIFT_DAYS:
        raise HTTPException(
            400, f"Dars ko'pi bilan {roles.RESCHEDULE_MAX_SHIFT_DAYS} "
                 f"kunga ko'chiriladi")

    # Bir dars ikki marta ko'chirilmaydi
    dup = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.group_id == g.id,
        models.LessonReschedule.from_date == payload.from_date,
        models.LessonReschedule.status.in_(
            roles.RESCHEDULE_DONE + ["pending"])).first()
    if dup:
        raise HTTPException(400, "Bu dars allaqachon ko'chirilgan yoki "
                                 "so'rov yuborilgan")

    quota = _reschedule_usage(db, t.id, payload.from_date)
    # Kvota ichida bo'lsa — avtomat. Tashqarisida bo'lsa tasdiqqa
    # yuboriladi, lekin BLOKLANMAYDI: haqiqiy sabab bo'lishi mumkin.
    auto = quota["auto_ok"]
    r = models.LessonReschedule(
        group_id=g.id, teacher_id=t.id,
        from_date=payload.from_date, to_date=payload.to_date,
        from_time=payload.from_time or g.lesson_time,
        to_time=payload.to_time or g.lesson_time,
        reason=payload.reason, note=payload.note,
        status="auto" if auto else "pending",
        auto_approved=1 if auto else 0,
        requested_by=user.id)
    db.add(r); db.commit(); db.refresh(r)

    if auto:
        _apply_reschedule(db, r)
        db.commit()
    else:
        # HAR BIR tasdiqlovchiga alohida vazifa (2026-08-24,
        # Jahongir: "HR uchun dars tasdiqlash chiqmay qolibdi").
        # Ilgari _hr_task() faqat bitta odamga biriktirardi.
        _notify_reschedule_approvers(db, r, g, t)

    audit.log(db, user, entity="lesson_reschedule", action="create",
              entity_id=r.id, entity_label=f"{g.name} {payload.from_date}",
              note=("avtomat" if auto else "tasdiq kutmoqda"),
              commit=True)
    return {**_resch_out(db, r),
            "quota": _reschedule_usage(db, t.id, payload.from_date)}

def _sub_out(db: Session, s: models.Substitution) -> dict:
    g = db.query(models.Group).get(s.group_id)
    orig = (db.query(models.Teacher).get(s.original_teacher_id)
            if s.original_teacher_id else None)
    sub = (db.query(models.Teacher).get(s.substitute_teacher_id)
           if s.substitute_teacher_id else None)
    return {
        "id": s.id,
        "group_id": s.group_id, "group": g.name if g else None,
        "subject": (roles.SUBJECT_LABELS.get(g.subject or "", g.subject)
                    if g else None),
        "lesson_date": s.lesson_date.isoformat(),
        "lesson_time": s.lesson_time,
        "original_teacher": orig.full_name if orig else None,
        "original_teacher_id": s.original_teacher_id,
        "substitute_teacher": sub.full_name if sub else None,
        "substitute_teacher_id": s.substitute_teacher_id,
        "reason": s.reason,
        "reason_label": roles.RESCHEDULE_REASON_LABELS.get(s.reason or "",
                                                           "—"),
        "note": s.note,
        "status": s.status,
        "status_label": roles.SUB_STATUS_LABELS.get(s.status, "—"),
        "status_tone": roles.SUB_STATUS_TONE.get(s.status, "slate"),
        "open": s.status == "offered",
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }

@router.get("/api/me/substitutions")
def my_substitutions(db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.SELF_STATS))):
    """Menga taklif qilinganlar, men so'raganlarim va ochiq
    takliflar."""
    t = _my_teacher_or_404(db, user)
    today = date.today()

    mine = db.query(models.Substitution).filter(
        models.Substitution.original_teacher_id == t.id).order_by(
        models.Substitution.lesson_date.desc()).limit(40).all()
    for_me = db.query(models.Substitution).filter(
        models.Substitution.substitute_teacher_id == t.id).order_by(
        models.Substitution.lesson_date.desc()).limit(40).all()
    # Kimga biriktirilmagan ochiq takliflar — o'z filialida
    my_group_ids = [g.id for g in _my_groups(db, t.id)]
    open_q = db.query(models.Substitution).filter(
        models.Substitution.substitute_teacher_id.is_(None),
        models.Substitution.status == "offered",
        models.Substitution.lesson_date >= today,
        models.Substitution.original_teacher_id != t.id).all()
    open_rows = []
    for s in open_q:
        g = db.query(models.Group).get(s.group_id)
        if g and t.branch_id and g.branch_id != t.branch_id:
            continue
        open_rows.append(s)

    return {
        "my_requests": [_sub_out(db, s) for s in mine],
        "assigned_to_me": [_sub_out(db, s) for s in for_me],
        "open_offers": [_sub_out(db, s) for s in open_rows],
        "my_groups": [{"id": g.id, "name": g.name}
                      for g in _my_groups(db, t.id)],
        "reasons": [{"key": k, "label": l}
                    for k, l in roles.RESCHEDULE_REASONS],
        "hint": ("O'rinbosar dars o'tsa, ish haqi darsni haqiqatda "
                 "o'tgan ustozga yoziladi."),
    }

@router.post("/api/me/substitutions")
def my_substitution_add(payload: schemas.SubstitutionIn,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.SELF_STATS))):
    """O'rniga o'tishni so'rash. Kimni tanlamasa — ochiq taklif
    bo'ladi, boshqa ustozlar ko'radi."""
    t = _my_teacher_or_404(db, user)
    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if g.teacher_id != t.id:
        raise HTTPException(403, "Bu guruh sizniki emas")
    if payload.lesson_date < date.today():
        raise HTTPException(400, "O'tib ketgan darsga o'rinbosar "
                                 "so'ralmaydi")
    if payload.substitute_teacher_id == t.id:
        raise HTTPException(400, "O'zingizni o'rinbosar qila olmaysiz")

    dup = db.query(models.Substitution).filter(
        models.Substitution.group_id == g.id,
        models.Substitution.lesson_date == payload.lesson_date,
        models.Substitution.status.in_(["offered", "accepted"])).first()
    if dup:
        raise HTTPException(400, "Bu darsga so'rov allaqachon bor")

    s = models.Substitution(
        group_id=g.id, lesson_date=payload.lesson_date,
        lesson_time=payload.lesson_time or g.lesson_time,
        original_teacher_id=t.id,
        substitute_teacher_id=payload.substitute_teacher_id,
        reason=payload.reason, note=payload.note,
        status="offered", created_by=user.id)
    db.add(s); db.commit(); db.refresh(s)

    _hr_task(db, title=f"O'rinbosar so'rovi #{s.id}",
             body=(f"{t.full_name} — {g.name}, {payload.lesson_date}. "
                   + ("Aniq ustoz taklif qilindi."
                      if payload.substitute_teacher_id
                      else "Ochiq taklif: hali hech kim olmagan.")),
             to_roles=roles.SUBSTITUTION_MANAGE,
             branch_id=g.branch_id, days=1)
    db.commit()
    audit.log(db, user, entity="substitution", action="create",
              entity_id=s.id, entity_label=f"{g.name} {payload.lesson_date}",
              commit=True)
    return _sub_out(db, s)

@router.post("/api/me/substitutions/{sid}/decide")
def my_substitution_decide(sid: int, payload: schemas.SubstitutionDecision,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.SELF_STATS))):
    """Ustoz taklifni qabul qiladi, rad etadi yoki o'z so'rovini
    bekor qiladi."""
    t = _my_teacher_or_404(db, user)
    s = db.query(models.Substitution).get(sid)
    if not s:
        raise HTTPException(404, "Topilmadi")
    if payload.decision not in ("accepted", "declined", "cancelled"):
        raise HTTPException(400, "Noma'lum qaror")

    if payload.decision == "cancelled":
        if s.original_teacher_id != t.id:
            raise HTTPException(403, "Faqat o'z so'rovingizni bekor "
                                     "qilasiz")
        if s.status not in ("offered", "accepted"):
            raise HTTPException(400, "Bu so'rov yopilgan")
        s.status = "cancelled"
    else:
        if s.status != "offered":
            raise HTTPException(400, "Bu taklif allaqachon hal qilingan")
        if s.original_teacher_id == t.id:
            raise HTTPException(400, "O'z so'rovingizni o'zingiz qabul "
                                     "qila olmaysiz")
        # Ochiq taklif bo'lsa qabul qilgan odam o'rinbosar bo'ladi
        if s.substitute_teacher_id and s.substitute_teacher_id != t.id:
            raise HTTPException(403, "Bu taklif boshqa ustozga berilgan")
        if payload.decision == "accepted":
            s.substitute_teacher_id = t.id
            s.status = "accepted"
            # Ish haqi to'g'ri odamga tushishi uchun darsning ustozi
            # almashtiriladi
            ls = db.query(models.Lesson).filter(
                models.Lesson.group_id == s.group_id,
                models.Lesson.date == s.lesson_date).first()
            if ls and not ls.held:
                ls.teacher_id = t.id
        else:
            s.status = "declined"
    s.decided_at = datetime.utcnow()
    s.note = ((s.note or "") + (f" · {payload.note}" if payload.note
                                else "")).strip() or None
    db.commit()
    audit.log(db, user, entity="substitution", action=payload.decision,
              entity_id=sid, commit=True)
    return _sub_out(db, s)

@router.get("/api/me/book-orders")
def my_book_orders(db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.SELF_STATS))):
    t = _my_teacher_or_404(db, user)
    rows = db.query(models.BookOrder).filter(
        models.BookOrder.teacher_id == t.id).order_by(
        models.BookOrder.id.desc()).limit(60).all()
    return {
        "rows": [_book_out(db, o) for o in rows],
        "groups": [{"id": g.id, "name": g.name}
                   for g in _my_groups(db, t.id)],
        "urgencies": [{"key": k, "label": l, "tone": tn, "days": d}
                      for k, l, tn, d in roles.BOOK_URGENCY],
        "hint": ("So'rov yuborilgach filial rahbariga vazifa bo'lib "
                 "boradi — og'zaki aytilgan iltimos yo'qoladi, vazifa "
                 "yo'qolmaydi."),
    }

@router.post("/api/me/book-orders")
def my_book_order_add(payload: schemas.BookOrderIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SELF_STATS))):
    t = _my_teacher_or_404(db, user)
    items = [i for i in (payload.items or []) if (i.title or "").strip()]
    if not items:
        raise HTTPException(400, "Kamida bitta kitob kiriting")
    if any(i.qty is None or i.qty < 1 for i in items):
        raise HTTPException(400, "Har bir kitob uchun soni 1 dan kam "
                                 "bo'lmasin")
    if payload.urgency and payload.urgency not in roles.BOOK_URGENCY_LABELS:
        raise HTTPException(400, "Noma'lum shoshilinchlik")

    g = db.query(models.Group).get(payload.group_id) \
        if payload.group_id else None
    if g and g.teacher_id != t.id:
        raise HTTPException(403, "Bu guruh sizniki emas")

    o = models.BookOrder(
        teacher_id=t.id, requested_by=user.id,
        branch_id=t.branch_id, group_id=payload.group_id,
        needed_by=payload.needed_by, urgency=payload.urgency or "normal",
        note=payload.note, status="new")
    db.add(o); db.commit(); db.refresh(o)
    _ensure_public_id(db, "book_order", o)
    for i in items:
        db.add(models.BookOrderItem(
            order_id=o.id, title=i.title.strip(), level=i.level,
            qty=int(i.qty), consumable_id=i.consumable_id, note=i.note))
    db.commit()

    # Filial rahbariga vazifa
    lines = "\n".join(f"· {i.title}"
                      + (f" ({i.level})" if i.level else "")
                      + f" — {int(i.qty)} dona" for i in items)
    task = models.Task(
        title=f"Kitob buyurtmasi {o.public_id}",
        description=(f"{t.full_name} so'radi"
                     + (f" · {g.name}" if g else "") + ".\n" + lines
                     + (f"\nKerak: {payload.needed_by}"
                        if payload.needed_by else "")
                     + (f"\nIzoh: {payload.note}" if payload.note else "")),
        assignee_id=_book_owner_id(db, t.branch_id),
        branch_id=t.branch_id,
        deadline=payload.needed_by or (
            date.today() + timedelta(
                days=roles.BOOK_URGENCY_DAYS.get(o.urgency, 7))),
        priority="high" if o.urgency == "urgent" else "normal",
        source="manual", created_by="Tizim")
    db.add(task); db.flush()
    _ensure_public_id(db, "task", task)
    o.task_id = task.id
    db.commit()

    audit.log(db, user, entity="book_order", action="create",
              entity_id=o.id, entity_label=o.public_id,
              note=f"{sum(int(i.qty) for i in items)} dona kitob",
              commit=True)
    return _book_out(db, o)

def _book_owner_id(db: Session, branch_id) -> int | None:
    """Kitob buyurtmasi kimga tushadi: filial rahbari, bo'lmasa
    xo'jalik menejeri, bo'lmasa asoschi."""
    for role in (roles.BRANCH_MANAGER, roles.FACILITY_MANAGER,
                 roles.FOUNDER):
        q = db.query(models.User).filter(models.User.role == role,
                                         models.User.is_active == 1)
        if branch_id and role == roles.BRANCH_MANAGER:
            u = q.filter(models.User.branch_id == branch_id).first()
        else:
            u = q.first()
        if u:
            return u.id
    return None

def _month_attendance(db: Session, group_ids: list, start: date,
                      end: date) -> dict:
    """Davr ichidagi davomat va uy vazifasi foizi."""
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson,
                  models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Lesson.group_id.in_(group_ids or [-1]),
                    models.Lesson.held == 1,
                    models.Lesson.date >= start,
                    models.Lesson.date <= end).all())
    total = len(rows)
    present = sum(1 for a, _ in rows if a.present)
    hw_rows = [a for a, _ in rows if a.homework is not None]
    hw_done = sum(1 for a in hw_rows if a.homework == 1)
    hw_partial = sum(1 for a in hw_rows if a.homework == 2)
    return {
        "marks": total,
        "present": present,
        "percent": round(present / total * 100, 1) if total else None,
        "homework_checked": len(hw_rows),
        "homework_done": hw_done,
        "homework_percent": (round(hw_done / len(hw_rows) * 100, 1)
                             if hw_rows else None),
        "homework_partial": hw_partial,
    }

def _streak_from_marks(marks: list) -> int:
    """Oxiridan boshlab ketma-ket nechta dars qoldirgan."""
    n = 0
    for present in reversed(marks):
        if present:
            break
        n += 1
    return n

def _teacher_dashboard(db: Session, user: models.User):
    """Ustozning dashboard bloki. Mavjud /api/me/dashboard ichiga
    qo'shiladi — ustoz uchun ikkinchi so'rov yuborilmaydi."""
    t = _teacher_of_user(db, user)
    if not t:
        return None
    groups = _cabinet_groups(db, user, t)
    gids = [g.id for g in groups]
    gname = {g.id: g.name for g in groups}
    today = date.today()
    month_start = today.replace(day=1)
    prev_end = month_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)

    # ---- 1. DAVOMAT ----
    this_month = _month_attendance(db, gids, month_start, today)
    last_month = _month_attendance(db, gids, prev_start, prev_end)

    # ---- Guruh kesimi ----
    per_group = {}
    for gid in gids:
        per_group[gid] = _month_attendance(db, [gid], month_start, today)

    students = db.query(models.Student).filter(
        models.Student.group_id.in_(gids or [-1]),
        models.Student.status == "active").all()
    sids = [s.id for s in students]
    sname = {s.id: s.full_name for s in students}
    sgroup = {s.id: s.group_id for s in students}

    # O'quvchi bo'yicha barcha belgilar (sana bo'yicha tartibda)
    all_marks = (db.query(models.Attendance, models.Lesson)
                 .join(models.Lesson,
                       models.Attendance.lesson_id == models.Lesson.id)
                 .filter(models.Attendance.student_id.in_(sids or [-1]),
                         models.Lesson.held == 1)
                 .order_by(models.Lesson.date, models.Lesson.id).all())
    by_student: dict = {}
    for a, ls in all_marks:
        by_student.setdefault(a.student_id, []).append((ls.date, a))

    alerts = []
    risk_students = []

    for sid, items in by_student.items():
        recent = [x for x in items if x[0] >= today - timedelta(days=90)]
        marks = [bool(a.present) for _d, a in recent]
        pct = (round(sum(marks) / len(marks) * 100, 1) if marks else None)

        # ---- Ogohlantirish: ketma-ket 2 dars ----
        streak = _streak_from_marks(marks)
        if streak >= roles.ABSENT_STREAK_ALERT:
            alerts.append({
                "kind": "absent_streak",
                "student_id": sid, "student": sname.get(sid),
                "group_id": sgroup.get(sid),
                "group": gname.get(sgroup.get(sid)),
                "detail": f"Ketma-ket {streak} dars kelmadi",
                "since": recent[-streak][0].isoformat() if recent else None,
            })

        # ---- Ogohlantirish: natija keskin tushdi ----
        grades = [g.score for g in db.query(models.DailyGrade)
                  .join(models.Lesson,
                        models.DailyGrade.lesson_id == models.Lesson.id)
                  .filter(models.DailyGrade.student_id == sid)
                  .order_by(models.Lesson.date,
                            models.Lesson.id).all() if g.score is not None]
        w = roles.SCORE_DROP_WINDOW
        if len(grades) >= w * 2:
            new_avg = sum(grades[-w:]) / w
            old_avg = sum(grades[-w * 2:-w]) / w
            drop = round(old_avg - new_avg, 1)
            if drop >= roles.SCORE_DROP_POINTS:
                alerts.append({
                    "kind": "score_drop",
                    "student_id": sid, "student": sname.get(sid),
                    "group_id": sgroup.get(sid),
                    "group": gname.get(sgroup.get(sid)),
                    "detail": (f"O'rtacha baho {round(old_avg, 1)} dan "
                               f"{round(new_avg, 1)} ga tushdi"),
                })

        if pct is not None and pct < roles.STUDENT_RISK_ATTENDANCE \
                and len(marks) >= 4:
            risk_students.append({
                "student_id": sid, "student": sname.get(sid),
                "group": gname.get(sgroup.get(sid)),
                "attendance_percent": pct,
                "missed": len(marks) - sum(marks),
                "absent_streak": streak,
            })
    risk_students.sort(key=lambda r: r["attendance_percent"])

    # ---- Ogohlantirish: guruh davomati past ----
    for gid, st in per_group.items():
        if st["percent"] is not None and \
                st["percent"] < roles.GROUP_ATTENDANCE_MIN:
            alerts.append({
                "kind": "group_attendance",
                "group_id": gid, "group": gname.get(gid),
                "detail": f"Shu oyda davomat {st['percent']}%",
            })

    # ---- Ogohlantirish: uy vazifasi pasaydi ----
    if this_month["homework_percent"] is not None and \
            last_month["homework_percent"] is not None:
        drop = round(last_month["homework_percent"]
                     - this_month["homework_percent"], 1)
        if drop >= roles.HOMEWORK_DROP_PERCENT:
            alerts.append({
                "kind": "homework_drop",
                "detail": (f"O'tgan oy {last_month['homework_percent']}%, "
                           f"shu oyda {this_month['homework_percent']}%"),
            })

    # ---- Ogohlantirish: 30 kundan beri o'sish yo'q ----
    for gid in gids:
        recent = (db.query(models.DailyGrade, models.Lesson)
                  .join(models.Lesson,
                        models.DailyGrade.lesson_id == models.Lesson.id)
                  .filter(models.Lesson.group_id == gid,
                          models.Lesson.date >= today - timedelta(
                              days=roles.NO_GROWTH_DAYS * 2))
                  .order_by(models.Lesson.date).all())
        cut = today - timedelta(days=roles.NO_GROWTH_DAYS)
        older = [g.score for g, ls in recent
                 if ls.date < cut and g.score is not None]
        newer = [g.score for g, ls in recent
                 if ls.date >= cut and g.score is not None]
        if len(older) >= roles.NO_GROWTH_MIN_LESSONS and \
                len(newer) >= roles.NO_GROWTH_MIN_LESSONS:
            before = sum(older) / len(older)
            after = sum(newer) / len(newer)
            if after <= before:
                alerts.append({
                    "kind": "no_growth",
                    "group_id": gid, "group": gname.get(gid),
                    "detail": (f"O'rtacha baho {round(before, 1)} → "
                               f"{round(after, 1)} — o'sish yo'q"),
                })

    # ---- Ogohlantirish: dars bo'ldi, davomat yo'q ----
    past = (db.query(models.Lesson)
            .filter(models.Lesson.group_id.in_(gids or [-1]),
                    models.Lesson.date <= today,
                    models.Lesson.date >= today - timedelta(days=30))
            .order_by(models.Lesson.date.desc()).all())
    marked = {r[0] for r in db.query(models.Attendance.lesson_id)
              .filter(models.Attendance.lesson_id.in_(
                  [l.id for l in past] or [-1])).distinct().all()}
    for ls in past:
        if ls.id in marked:
            continue
        # Bugungi dars uchun biroz vaqt beriladi — dars endi
        # tugagan bo'lishi mumkin
        if ls.date == today:
            g = next((x for x in groups if x.id == ls.group_id), None)
            mins = roles.time_to_minutes(g.lesson_time) if g else None
            now_local = roles.local_now()
            if mins is not None and (now_local.hour * 60 + now_local.minute) \
                    < mins + roles.ATTENDANCE_GRACE_HOURS * 60:
                continue
        alerts.append({
            "kind": "attendance_missing",
            "group_id": ls.group_id, "group": gname.get(ls.group_id),
            "lesson_id": ls.id,
            "detail": f"{ls.date.isoformat()} darsi belgilanmagan",
            "date": ls.date.isoformat(),
        })

    for a in alerts:
        a["label"] = roles.ALERT_LABELS.get(a["kind"], a["kind"])
        a["tone"] = roles.ALERT_TONE.get(a["kind"], "slate")
        a["advice"] = roles.ALERT_ADVICE.get(a["kind"], "")
    order = {k: i for i, (k, _l, _t, _h) in enumerate(roles.TEACHER_ALERTS)}
    alerts.sort(key=lambda a: order.get(a["kind"], 99))

    # ---- 3. RIVOJLANISH VAZIFALARI ----
    study = db.query(models.TeacherStudyItem).filter(
        models.TeacherStudyItem.teacher_id == t.id).all()
    study_rows = [{
        "id": i.id, "stage": i.stage, "kind": i.kind,
        "kind_label": "Kitob" if i.kind == "book" else "Podkast",
        "title": i.title, "done": bool(i.done),
        "done_at": i.done_at.isoformat() if i.done_at else None,
    } for i in study]
    study_left = [r for r in study_rows if not r["done"]]

    my_tasks = (db.query(models.Task)
                .filter(models.Task.assignee_id == user.id,
                        models.Task.status.notin_(["done", "cancelled"]))
                .order_by(models.Task.deadline).limit(20).all())
    task_rows = [{
        "id": x.id, "public_id": x.public_id, "title": x.title,
        "deadline": x.deadline.isoformat() if x.deadline else None,
        "overdue": bool(x.deadline and x.deadline < today),
        "priority": x.priority,
    } for x in my_tasks]

    # Dars kuzatuvlari — metodik topshiriq manbai
    obs = (db.query(models.LessonObservation)
           .filter(models.LessonObservation.teacher_id == t.id)
           .order_by(models.LessonObservation.id.desc()).limit(3).all())

    by_kind: dict = {}
    for a in alerts:
        by_kind[a["kind"]] = by_kind.get(a["kind"], 0) + 1

    # Yo'qlama intizomi — joriy oy. Jahongir (2026-08-12): "intizom
    # foizi ... o'ziga ham ko'rinib tursin, qancha vaqt kechikib
    # yo'qlama qilyapti, qancha o'z vaqtida".
    try:
        _disc = _discipline_one(db, t.id, month_start,
                                today + timedelta(days=1))
    except Exception:
        _disc = None

    return {
        "teacher": {"id": t.id, "name": t.full_name},
        "discipline": _disc,
        "attendance": {
            "percent": this_month["percent"],
            "last_month": last_month["percent"],
            "change": (round(this_month["percent"] - last_month["percent"], 1)
                       if this_month["percent"] is not None
                       and last_month["percent"] is not None else None),
            "marks": this_month["marks"],
            "present": this_month["present"],
            "homework_percent": this_month["homework_percent"],
            "homework_last_month": last_month["homework_percent"],
            "homework_checked": this_month["homework_checked"],
            "month": month_start.isoformat(),
        },
        "groups": [{
            "id": gid, "name": gname.get(gid),
            "percent": per_group[gid]["percent"],
            "homework_percent": per_group[gid]["homework_percent"],
            "low": (per_group[gid]["percent"] is not None
                    and per_group[gid]["percent"]
                    < roles.GROUP_ATTENDANCE_MIN),
        } for gid in gids],
        "risk_students": risk_students[:20],
        "risk_count": len(risk_students),
        "alerts": alerts[:40],
        "alert_count": len(alerts),
        "alerts_by_kind": [{
            "key": k, "label": lbl, "tone": tn,
            "count": by_kind.get(k, 0),
        } for k, lbl, tn, _h in roles.TEACHER_ALERTS],
        "development": {
            "study": study_rows,
            "study_left": len(study_left),
            "study_total": len(study_rows),
            "tasks": task_rows,
            "tasks_overdue": sum(1 for x in task_rows if x["overdue"]),
            "observations": [_observation_out(db, o) for o in obs],
        },
        "thresholds": {
            "absent_streak": roles.ABSENT_STREAK_ALERT,
            "group_attendance": roles.GROUP_ATTENDANCE_MIN,
            "student_attendance": roles.STUDENT_RISK_ATTENDANCE,
            "homework_drop": roles.HOMEWORK_DROP_PERCENT,
            "no_growth_days": roles.NO_GROWTH_DAYS,
        },
        "hint": ("Har bir ogohlantirish — bugun qilinadigan ish. "
                 "Yonida nima qilish kerakligi yozilgan."),
    }

def _active_count(db: Session, group_id: int) -> int:
    return db.query(models.Student).filter(
        models.Student.group_id == group_id,
        models.Student.status == "active").count()

@router.get("/api/me/exam-orders")
def my_exam_orders(db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.EXAM_ORDER_CREATE))):
    """Ustozning o'z buyurtmalari va yangi buyurtma uchun ma'lumot."""
    t = _teacher_of_user(db, user)
    q = db.query(models.ExamOrder)
    if t:
        q = q.filter(models.ExamOrder.teacher_id == t.id)
        groups = _my_groups(db, t.id)
    else:
        # O'quv bo'limi / rahbariyat: filial bo'yicha
        q = scope_to_branch(q, models.ExamOrder, user)
        gq = scope_to_branch(db.query(models.Group), models.Group, user)
        groups = gq.order_by(models.Group.name).all()

    rows = q.order_by(models.ExamOrder.id.desc()).limit(100).all()
    return {
        "rows": [_exam_order_out(db, o) for o in rows],
        "groups": [{"id": g.id, "name": g.name, "level": g.level,
                    "time": g.lesson_time,
                    "students": _active_count(db, g.id)} for g in groups],
        **_exam_order_form(db, user),
        "hint": ("Buyurtma yuborilgach filialingizdagi examinerlarga "
                 "vazifa bo'lib boradi. Kim qabul qilgani shu yerda "
                 "ko'rinadi."),
    }

@router.post("/api/me/exam-orders")
def my_exam_order_add(payload: schemas.ExamOrderIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.EXAM_ORDER_CREATE))):
    g = _get_group_in_scope(db, payload.group_id, user)
    t = _teacher_of_user(db, user)

    today = roles.local_today()
    notice = (payload.date - today).days
    if notice < roles.EXAM_ORDER_MIN_NOTICE_DAYS:
        raise HTTPException(
            400, f"Imtihon kamida {roles.EXAM_ORDER_MIN_NOTICE_DAYS} kun "
                 f"oldin so'ralishi kerak — examinerning ham jadvali bor")
    if notice > roles.EXAM_ORDER_MAX_AHEAD_DAYS:
        raise HTTPException(
            400, f"Ko'pi bilan {roles.EXAM_ORDER_MAX_AHEAD_DAYS} kun "
                 f"oldin buyurtma qilinadi")
    if payload.kind not in roles.EXAM_KINDS:
        raise HTTPException(400, "Test turi noto'g'ri")
    if payload.kind == "unit":
        # Qaysi unit ekani MAJBURIY - examiner shu unitning testini
        # tayyorlab keladi (Jahongir, 2026-08-11)
        if not payload.unit_no:
            raise HTTPException(
                400, "Qaysi unit ekanini belgilang - examiner shu "
                     "unitning testini tayyorlab keladi")
        if not (1 <= payload.unit_no <= roles.UNIT_COUNT):
            raise HTTPException(400, f"Unit 1 dan {roles.UNIT_COUNT} gacha")

    dup = db.query(models.ExamOrder).filter(
        models.ExamOrder.group_id == g.id,
        models.ExamOrder.date == payload.date,
        models.ExamOrder.status.in_(roles.EXAM_ORDER_OPEN)).first()
    if dup:
        raise HTTPException(
            400, "Bu guruhga shu kunga buyurtma allaqachon yuborilgan")

    o = models.ExamOrder(
        group_id=g.id,
        teacher_id=t.id if t else g.teacher_id,
        branch_id=g.branch_id,
        date=payload.date,
        time=payload.time or g.lesson_time,
        kind=payload.kind,
        unit_no=payload.unit_no,
        # AVTOMAT: ustoz o'quvchi sonini qo'lda yozmaydi
        students_count=_active_count(db, g.id),
        note=payload.note,
        status="new",
        requested_by=user.id)
    db.add(o); db.commit(); db.refresh(o)
    _ensure_public_id(db, "exam_order", o)
    db.commit(); db.refresh(o)

    out = _exam_order_out(db, o)
    # So'rov FILIALDAGI BARCHA examinerlarga alohida vazifa bo'lib
    # tushadi (Jahongir: "shu filialdagi examinerlaga bildirishnoma
    # bo'lib tushsin, xabar kelsin"). Ilgari bitta odamga (ko'pincha
    # asoschiga) tushardi - examinerlar ko'rmay qolardi.
    # Qo'shimcha lavozimi examiner bo'lganlar ham (2026-10-07)
    _exs = (db.query(models.User)
            .filter(_any_role_cond((roles.EXAMINER, roles.HEAD_EXAMINER)),
                    models.User.is_active == 1).all())
    _extra = {ub.user_id for ub in db.query(models.UserBranch)
              .filter(models.UserBranch.branch_id == g.branch_id).all()}
    _local = [u for u in _exs
              if u.branch_id == g.branch_id or u.id in _extra
              or not u.branch_id]
    _targets = _local or _exs  # filialda examiner bo'lmasa - hammasiga
    _days = max(1, (payload.date - today).days)
    for _u in _targets:
        _hr_task_for(
            db, _u.id,
            title=f"Imtihon buyurtmasi {o.public_id} — {_u.full_name}",
            body=out["message"],
            branch_id=g.branch_id, days=_days)
    if not _targets:
        _hr_task(db, title=f"Imtihon buyurtmasi {o.public_id}",
                 body=out["message"],
                 to_roles=roles.EXAM_ORDER_ACCEPT,
                 branch_id=g.branch_id, days=_days, priority="high")
    db.commit()

    audit.log(db, user, entity="exam_order", action="create",
              entity_id=o.id, entity_label=g.name,
              branch_id=g.branch_id,
              new_value=f"{roles.uz_date_full(o.date)} {o.time or ''}".strip(),
              commit=True)
    return out

@router.post("/api/me/exam-orders/{oid}/cancel")
def my_exam_order_cancel(oid: int, payload: schemas.ExamOrderDecision,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.EXAM_ORDER_CREATE))):
    o = db.query(models.ExamOrder).get(oid)
    if not o:
        raise HTTPException(404, "Buyurtma topilmadi")
    t = _teacher_of_user(db, user)
    if t and o.teacher_id != t.id:
        raise HTTPException(403, "Bu buyurtma sizniki emas")
    if o.status not in roles.EXAM_ORDER_OPEN:
        raise HTTPException(400, "Bu buyurtmani endi bekor qilib bo'lmaydi")
    o.status = "cancelled"
    o.decision_note = payload.note
    # Bekor qilingan buyurtma examinerlarda "kechikdi" bo'lib qolmasin
    _close_order_tasks(db, o, "ustoz buyurtmani bekor qildi")
    db.commit()
    audit.log(db, user, entity="exam_order", action="cancel",
              entity_id=o.id, note=payload.note, commit=True)
    return _exam_order_out(db, o)

@router.get("/api/me/support-busy")
def my_support_busy(db: Session = Depends(get_db),
                    user=Depends(require_role(roles.SUPPORT_TEACHER))):
    t = _my_teacher_or_404(db, user)
    rows = (db.query(models.SupportBusy)
            .filter(models.SupportBusy.teacher_id == t.id)
            .order_by(models.SupportBusy.start).all())
    return [{"id": r.id, "days": r.days, "start": r.start,
             "end": r.end, "note": r.note} for r in rows]

@router.post("/api/me/support-busy")
def add_support_busy(payload: schemas.SupportBusyIn,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(roles.SUPPORT_TEACHER))):
    """Support o'zi: "bu vaqtda menga dars qo'yilmasin" deb belgilaydi.
    Support manager guruh biriktirayotganda shu ko'rinib turadi."""
    t = _my_teacher_or_404(db, user)
    s, e = _time_to_min(payload.start), _time_to_min(payload.end)
    if s is None or e is None or s >= e:
        raise HTTPException(400, "Vaqt noto'g'ri — masalan 14:00 va 16:00")
    days = [d for d in payload.days.split(",")
            if d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")]
    if not days:
        raise HTTPException(400, "Kamida bitta kun tanlang")
    r = models.SupportBusy(teacher_id=t.id, days=",".join(days),
                           start=payload.start.strip(),
                           end=payload.end.strip(),
                           note=(payload.note or "").strip() or None)
    db.add(r)
    db.commit()
    return {"ok": True, "id": r.id}

@router.delete("/api/me/support-busy/{bid}")
def del_support_busy(bid: int, db: Session = Depends(get_db),
                     user=Depends(require_role(roles.SUPPORT_TEACHER))):
    t = _my_teacher_or_404(db, user)
    r = db.query(models.SupportBusy).get(bid)
    if not r or r.teacher_id != t.id:
        raise HTTPException(404, "Yozuv topilmadi")
    db.delete(r)
    db.commit()
    return {"ok": True}

@router.get("/api/me/support-sessions")
def my_support_sessions(year: int | None = None, month: int | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(
                            roles.SUPPORT_TEACHER, *roles.FULL_ACCESS,
                            roles.ACADEMIC_HEAD))):
    """Support teacherning o'z seanslari va shu oy oyligi hisobi."""
    t = _my_teacher_or_404(db, user) if user.role == roles.SUPPORT_TEACHER \
        else _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Ustoz kartasi topilmadi")
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    out = _support_month(db, t.id, y, m)
    gq = scope_to_branch(db.query(models.Group), models.Group, user)
    out["all_groups"] = [{"id": g.id, "name": g.name}
                         for g in gq.order_by(models.Group.name).all()]
    out["max_hours"] = roles.SUPPORT_SESSION_MAX_HOURS
    out["max_students"] = roles.SUPPORT_SESSION_MAX_STUDENTS
    out["hint"] = (
        "Har darsni o'sha kuni kiriting: guruh, boshlanish-tugash "
        "vaqti, o'quvchilar soni. Oylik avtomat hisoblanadi: "
        "(soat x 0.30 + o'quvchi x 0.20 + test koeffitsiyenti x 0.50) "
        "x 10 000. Kamida 400 000, ko'pi bilan 1 500 000.")
    # VOLONTYORGA OYLIK HISOBLANMAYDI (2026-09-23, Jahongir:
    # "valantyor supportlar uchun oylik hisoblanmasligi kerak").
    # Seanslar baribir yoziladi - ular tajriba va daraja ko'tarish
    # uchun kerak, faqat pul hisobi 0 bo'ladi.
    if _is_volunteer(db, user):
        out["volunteer"] = True
        out["salary"] = 0
        out["raw"] = 0
        out["clamped_min"] = False
        out["clamped_max"] = False
        out["hint"] = (
            "Har darsni o'sha kuni kiriting: guruh, boshlanish-tugash "
            "vaqti, o'quvchilar soni. Volontyor bosqichida oylik "
            "hisoblanmaydi - seanslaringiz tajriba va keyingi "
            "darajaga o'tish uchun yoziladi.")
        out["volunteer_hint"] = _VOLUNTEER_HINT
    return out

@router.post("/api/me/support-sessions")
def my_support_session_add(payload: schemas.SupportSessionIn,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               roles.SUPPORT_TEACHER,
                               *roles.PAST_ATTENDANCE))):
    """Seans kiritish. Sana qoidalari yoqlamadagidek: kelajakka hech
    kim, o'tgan kunga faqat asoschi va o'quv bo'limi rahbari."""
    t = _my_teacher_or_404(db, user) if user.role == roles.SUPPORT_TEACHER \
        else _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Ustoz kartasi topilmadi")

    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")

    today = roles.local_today()
    d = payload.date or today
    if d > today:
        raise HTTPException(400, "Hali kelmagan kunga seans kiritilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunga faqat asoschi va o'quv bo'limi "
                 "rahbari kirita oladi — darsni o'sha kuni kiriting")

    s_min = roles.hhmm_minutes(payload.start_time)
    e_min = roles.hhmm_minutes(payload.end_time)
    if s_min is None or e_min is None:
        raise HTTPException(400, "Vaqt SS:DD ko'rinishida bo'lsin, "
                                 "masalan 14:30")
    if e_min <= s_min:
        raise HTTPException(400, "Tugash vaqti boshlanishdan keyin "
                                 "bo'lishi kerak")
    minutes = e_min - s_min
    if minutes > roles.SUPPORT_SESSION_MAX_HOURS * 60:
        raise HTTPException(
            400, f"Bitta seans {roles.SUPPORT_SESSION_MAX_HOURS} "
                 f"soatdan oshmaydi — xato kiritmadingizmi?")
    if not (1 <= payload.students_count
            <= roles.SUPPORT_SESSION_MAX_STUDENTS):
        raise HTTPException(
            400, f"O'quvchilar soni 1 dan "
                 f"{roles.SUPPORT_SESSION_MAX_STUDENTS} gacha")

    # Bir kunda bitta guruhga ikki marta kiritilmaydi — oylik
    # ikkilanmasin
    # Yakka darslar bu qoidaga kirmaydi (2026-09-23): o'sha guruhdagi
    # bitta o'quvchi bilan alohida shug'ullanish guruh darsini
    # yozishga to'sqinlik qilmasligi kerak.
    dup = db.query(models.SupportSession).filter(
        models.SupportSession.teacher_id == t.id,
        models.SupportSession.group_id == g.id,
        models.SupportSession.student_id.is_(None),
        models.SupportSession.date == d).first()
    if dup:
        raise HTTPException(400, "Bu guruh uchun bugun seans allaqachon "
                                 "kiritilgan")

    r = models.SupportSession(
        teacher_id=t.id, group_id=g.id, branch_id=g.branch_id,
        date=d, start_time=payload.start_time,
        end_time=payload.end_time, minutes=minutes,
        students_count=payload.students_count, note=payload.note,
        created_by=user.id)
    db.add(r); db.commit(); db.refresh(r)
    audit.log(db, user, entity="support_session", action="create",
              entity_id=r.id, entity_label=g.name,
              branch_id=g.branch_id,
              new_value=f"{payload.start_time}-{payload.end_time} · "
                        f"{payload.students_count} o'quvchi",
              commit=True)
    return _support_session_out(db, r)

# =====================================================================
#  YAKKA DARSLAR (2026-09-23)
#
#  Ustoz orqada qolgan o'quvchisini supportga biriktiradi. Support shu
#  yerda o'sha o'quvchilarni ko'radi va bitta tugma bilan darsni
#  yozadi: yo'qlama belgisi HAM, seans HAM bir vaqtda tushadi -
#  shunda yo'qlama va pul hisobi bir-biridan ajralib qolmaydi.
#
#  O'quvchidan qo'shimcha pul olinmaydi. Supportga esa yakka dars
#  soati ikki barobar ball beradi (roles.SUPPORT_HOURS_W_SMALL).
# =====================================================================
def _solo_month_rows(db: Session, teacher_id: int, sid: int,
                     y: int, m: int) -> list:
    start, end = billing.month_bounds(y, m)
    ses = {r.date: r for r in db.query(models.SupportSession)
           .filter(models.SupportSession.teacher_id == teacher_id,
                   models.SupportSession.student_id == sid,
                   models.SupportSession.date >= start,
                   models.SupportSession.date <= end).all()}
    _SA = models.SupportAttendance
    marks = (db.query(_SA)
             .filter(_SA.student_id == sid, _SA.date >= start,
                     _SA.date <= end)
             .order_by(_SA.date).all())
    out = []
    for a in marks:
        r = ses.get(a.date)
        out.append({
            "date": a.date.isoformat(),
            "present": bool(a.present),
            "hours": round((r.minutes or 0) / 60, 2) if r else 0,
            "session_id": r.id if r else None,
        })
    return out


@router.get("/api/me/support-solo")
def my_solo_students(year: int | None = None, month: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(
                         roles.SUPPORT_TEACHER, *roles.ACADEMIC_ACCESS))):
    """Supportga yakka biriktirilgan o'quvchilar va shu oygi darslari."""
    t = _teacher_of_user(db, user)
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    q = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.student_id.isnot(None)))
    if user.role == roles.SUPPORT_TEACHER:
        q = q.filter(models.SupportAssignment.user_id == user.id)
    rows = []
    for a in q.all():
        st = db.query(models.Student).get(a.student_id)
        if not st or st.status != "active":
            continue
        g = db.query(models.Group).get(st.group_id) if st.group_id else None
        lessons = (_solo_month_rows(db, t.id, st.id, y, m)
                   if t else [])
        rows.append({
            "assignment_id": a.id,
            "student_id": st.id,
            "name": st.full_name,
            "group_id": st.group_id,
            "group": g.name if g else None,
            "days": a.days, "start": a.start, "end": a.end,
            "note": a.note,
            "lessons": lessons,
            "done": sum(1 for x in lessons if x["present"]),
            "missed": sum(1 for x in lessons if not x["present"]),
            "today_done": any(x["date"] == today.isoformat()
                              for x in lessons),
        })
    rows.sort(key=lambda r: r["name"])
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "hour_steps": roles.SUPPORT_SESSION_HOUR_STEPS,
        "hint": ("Yakka dars o'quvchiga pulsiz. Sizga esa bu soat ikki "
                 "barobar ball beradi — guruh darsi 0.30, yakka dars "
                 "0.60."),
    }


@router.post("/api/me/support-solo/{sid}/lesson")
def my_solo_lesson(sid: int, payload: dict = Body(...),
                   db: Session = Depends(get_db),
                   user=Depends(require_role(
                       roles.SUPPORT_TEACHER, *roles.PAST_ATTENDANCE))):
    """Yakka darsni yozish: keldi (seans + yo'qlama) yoki kelmadi
    (faqat yo'qlama, pul yozilmaydi)."""
    t = _my_teacher_or_404(db, user) if user.role == roles.SUPPORT_TEACHER \
        else _teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Ustoz kartasi topilmadi")
    st = db.query(models.Student).get(sid)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    a = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.student_id == sid,
                 models.SupportAssignment.user_id == (
                     user.id if user.role == roles.SUPPORT_TEACHER
                     else models.SupportAssignment.user_id)).first())
    if not a:
        raise HTTPException(403, "Bu o'quvchi sizga biriktirilmagan")

    today = roles.local_today()
    d = payload.get("date")
    d = date.fromisoformat(d) if d else today
    if d > today:
        raise HTTPException(400, "Hali kelmagan kunga dars yozilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(403, "O'tib ketgan kunga faqat asoschi va "
                                 "o'quv bo'limi rahbari kirita oladi")

    _SA = models.SupportAttendance
    dup = (db.query(_SA).filter(_SA.student_id == sid, _SA.date == d)
           .first())
    if dup and db.query(models.SupportSession).filter(
            models.SupportSession.teacher_id == t.id,
            models.SupportSession.student_id == sid,
            models.SupportSession.date == d).first():
        raise HTTPException(400, "Bu kunga dars allaqachon yozilgan")

    present = bool(payload.get("present", True))
    if dup:
        dup.present = 1 if present else 0
    else:
        db.add(_SA(group_id=st.group_id or 0, student_id=sid, date=d,
                   present=1 if present else 0,
                   note="Yakka dars", created_by=user.full_name))

    out_hours = 0.0
    if present:
        hours = payload.get("hours")
        if hours is None and a.start and a.end:
            s_min = roles.hhmm_minutes(a.start)
            e_min = roles.hhmm_minutes(a.end)
            if s_min is not None and e_min is not None and e_min > s_min:
                hours = round((e_min - s_min) / 60, 2)
        hours = float(hours or 1)
        if not (0 < hours <= roles.SUPPORT_SESSION_MAX_HOURS):
            raise HTTPException(
                400, f"Dars 0 dan {roles.SUPPORT_SESSION_MAX_HOURS} "
                     f"soatgacha bo'lsin")
        start = a.start or "00:00"
        s_min = roles.hhmm_minutes(start) or 0
        minutes = int(round(hours * 60))
        e_min = s_min + minutes
        g = db.query(models.Group).get(st.group_id) if st.group_id else None
        r = models.SupportSession(
            teacher_id=t.id, group_id=st.group_id, student_id=sid,
            branch_id=(g.branch_id if g else st.branch_id), date=d,
            start_time=start,
            end_time=f"{(e_min // 60) % 24:02d}:{e_min % 60:02d}",
            minutes=minutes, students_count=1,
            note=f"Yakka dars: {st.full_name}", created_by=user.id)
        db.add(r)
        out_hours = hours
    db.commit()
    audit.log(db, user, entity="support_session", action="create",
              entity_label=st.full_name, field="Yakka dars",
              new_value=("keldi" if present else "kelmadi"),
              branch_id=st.branch_id, commit=True)
    return {"ok": True, "present": present, "hours": out_hours,
            "date": d.isoformat()}


@router.delete("/api/me/support-sessions/{sid}")
def my_support_session_delete(sid: int, db: Session = Depends(get_db),
                              user=Depends(require_role(
                                  roles.SUPPORT_TEACHER,
                                  *roles.PAST_ATTENDANCE))):
    r = db.query(models.SupportSession).get(sid)
    if not r:
        raise HTTPException(404, "Seans topilmadi")
    t = _teacher_of_user(db, user)
    if user.role == roles.SUPPORT_TEACHER and (not t or r.teacher_id != t.id):
        raise HTTPException(403, "Bu seans sizniki emas")
    # O'z seansini faqat o'sha kuni o'chiradi — o'tgan kun pul hujjati
    if user.role == roles.SUPPORT_TEACHER and r.date != roles.local_today():
        raise HTTPException(403, "O'tgan kunning seansini faqat asoschi "
                                 "yoki o'quv bo'limi rahbari o'chiradi")
    db.delete(r); db.commit()
    audit.log(db, user, entity="support_session", action="delete",
              entity_id=sid, commit=True)
    return {"ok": True}

@router.get("/api/me/examiner-salary")
def my_examiner_salary(year: int | None = None, month: int | None = None,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(
                           roles.EXAMINER, roles.HEAD_EXAMINER))):
    """Examinerning o'z oyligi — imtihonlari kesimida, avtomat."""
    today = roles.local_today()
    out = _examiner_month(db, user.id, year or today.year,
                          month or today.month)
    # VOLONTYORGA OYLIK HISOBLANMAYDI (2026-09-23, Jahongir: supportdan
    # keyin "examinerlarga ham"). Imtihonlari va ballari ko'rinib
    # turadi - u ish qilgani va daraja ko'tarish shu yerdan ko'rinadi,
    # faqat pul hisobi 0 bo'ladi.
    if _is_volunteer(db, user):
        out["volunteer"] = True
        out["salary"] = 0
        out["raw"] = 0
        out["clamped_min"] = False
        out["clamped_max"] = False
        out["volunteer_hint"] = _VOLUNTEER_HINT
    from salary_coach import examiner_salary_goal
    out["goal"] = examiner_salary_goal(out, today)
    return out

@router.get("/api/me/junior-path")
def my_junior_path(db: Session = Depends(get_db),
                   user=Depends(require_role(roles.SUPPORT_TEACHER))):
    """Support teacher Junior teacher bo'lishi uchun nimalar kerak."""
    t = _teacher_of_user(db, user)
    months = t.support_months or 0
    if not months and t and t.hired_date:
        months = round((roles.local_today() - t.hired_date).days / 30, 1)
    items = [
        {"key": "cert",
         "label": "Sertifikat: CEFR B2 (kamida 55%)",
         "current": t.cert or "kiritilmagan",
         "value": t.cert_score, "target": 55.0,
         "done": bool(t.cert_score and t.cert_score >= 55)},
        {"key": "skill",
         "label": "Dars berish mahorati balli (kamida 75)",
         "current": t.skill_score, "value": t.skill_score, "target": 75.0,
         "done": bool(t.skill_score and t.skill_score >= 75)},
        {"key": "months",
         "label": "Support tajribasi (kamida 3 oy)",
         "current": months, "value": months, "target": 3.0,
         "done": months >= 3},
    ]
    return {
        "grade_label": "Support teacher",
        "target_label": "Junior teacher",
        "items": items,
        "done_count": len([i for i in items if i["done"]]),
        "total": len(items),
        "ready": all(i["done"] for i in items),
        "hint": ("Hammasi bajarilganda o'quv bo'limi rahbari sinov darsi "
                 "(kuzatuv) o'tkazadi va Junior teacher darajasiga "
                 "o'tkazish masalasini hal qiladi."),
    }

def _freeze_contacted(db: Session, s) -> bool:
    """Shu muzlatish bo'yicha "aloqaga chiqing" vazifasi bajarilganmi.
    Kalitli yangi vazifa, yoki kalitsiz eski vazifa — sarlavha bir xil va
    muddati muzlatish tugash sanasi (±1 kun)."""
    import common as _cm
    T = models.Task
    if db.query(T.id).filter(
            T.group_key.like(_cm.freeze_task_key(s.id, s.frozen_until) + "%"),
            T.status == "done").first():
        return True
    old = (db.query(T).filter(T.group_key.is_(None),
                              T.title == f"Muzlatilgan o'quvchi: {s.full_name}",
                              T.status == "done").all())
    return any(t.deadline and s.frozen_until
               and abs((t.deadline - s.frozen_until).days) <= 1 for t in old)


@router.get("/api/my/alerts")
def my_alerts(db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    today = roles.local_today()
    items = []

    # 1) Mening ochiq vazifalarim
    try:
        tq = db.query(models.Task).filter(
            models.Task.assignee_id == user.id,
            models.Task.status.notin_(("done", "cancelled")))
        open_tasks = tq.count()
        overdue = sum(1 for t in tq.all()
                      if t.deadline and t.deadline < today)
        if open_tasks:
            items.append({
                "icon": "task",
                "text": f"{open_tasks} ta ochiq vazifangiz bor"
                        + (f", {overdue} tasi muddati o'tgan" if overdue
                           else ""),
                "link": "/tasks",
                "tone": "red" if overdue else "amber",
            })
    except Exception:
        pass

    # 2) Muzlatilganlardan bugungacha qaytishi kerak bo'lganlar
    if user.role in tuple(roles.FREEZE_ROLES):
        fq = db.query(models.Student).filter(
            models.Student.status == "frozen",
            models.Student.frozen_until.isnot(None),
            models.Student.frozen_until <= today)
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            fq = fq.filter(_branch_in(db, user, models.Student.branch_id))
        back = fq.all()
        # Aloqa vazifasini biror admin "bajarildi" degan bo'lsa — filialdagi
        # HAMMA admindan yo'qoladi (2026-10-21, Jahongir: "qildim desa
        # o'sha filial adminlaridan ham olib tashlasin")
        back = [s for s in back if not _freeze_contacted(db, s)]
        for s in back[:5]:
            items.append({
                "icon": "freeze",
                "text": f"{s.full_name} — muzlatish muddati tugadi, "
                        "aloqaga chiqing",
                "link": f"/students/{s.id}",
                "tone": "sky",
            })
        if len(back) > 5:
            items.append({"icon": "freeze",
                          "text": f"...va yana {len(back) - 5} ta "
                                  "qaytishi kerak bo'lgan o'quvchi",
                          "link": "/students", "tone": "sky"})

    # 3) Qarzdorlar (pul bilan ishlaydiganlarga)
    if user.role in tuple(roles.CASH_ACCESS):
        bal = dict(
            db.query(models.Payment.student_id,
                     func.coalesce(func.sum(models.Payment.amount), 0.0))
            .group_by(models.Payment.student_id).all())
        sq = db.query(models.Student).filter(
            models.Student.status == "active")
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            sq = sq.filter(_branch_in(db, user, models.Student.branch_id))
        debtors = sum(1 for s in sq.all() if (bal.get(s.id, 0) or 0) < 0)
        if debtors:
            items.append({
                "icon": "money",
                "text": f"{debtors} ta qarzdor o'quvchi bor",
                "link": "/finance",
                "tone": "red",
            })

    # 4) Muddati yaqin hujjatlar (asoschi, o'quv rahbari, HR)
    if user.role in (roles.FOUNDER, roles.ACADEMIC_HEAD, roles.HR_MANAGER):
        try:
            soon = today + timedelta(days=14)
            dq = db.query(models.EmployeeDocument).filter(
                models.EmployeeDocument.expires_on.isnot(None),
                models.EmployeeDocument.expires_on <= soon).all()
            expiring = [d for d in dq if d.expires_on >= today]
            if expiring:
                items.append({
                    "icon": "doc",
                    "text": f"{len(expiring)} ta hujjat (shartnoma/"
                            "sertifikat) muddati 2 hafta ichida tugaydi",
                    "link": "/hr",
                    "tone": "amber",
                })
        except Exception:
            pass

    # 5) TUG'ILGAN KUN, YUBILEY VA TADBIRLAR (2026-10-05, Jahongir:
    #    "event manager va boshqa bayram bildirishnomalarida kimni
    #    tug'ilgan kuni yo yubileyi ekani ko'rinmayabdi, ustiga bossa
    #    batafsil ma'lumot chiqaradigan qilib ber").
    #    Ilgari faqat asoschi va HR ko'rardi, faqat BUGUNGI xodimlar,
    #    ko'pi bilan 3 ta. Endi har biri alohida qator — ism, kim
    #    ekani, qachon — va "detail" bilan: bosilganda to'liq ma'lumot
    #    va tayyor tabrik matni chiqadi.
    try:
        items += _celebration_alerts(db, user, today)
    except Exception:
        db.rollback()

    # 6) "SO'Z BILISH" SERTIFIKATLARI (2026-10-17): o'quvchi yuklagan va
    #    tekshiruvni kutayotganlar SONI — tasdiqlay oladigan xodimga, o'z
    #    chegarasida (ustoz — o'z guruhlari). Ism va ball yo'q.
    try:
        import wordbank_certs as _WCERT
        with db.begin_nested():
            it = _WCERT.pending_alert(db, user)
        if it:
            items.append(it)
    except Exception:
        pass

    return {"items": items, "count": len(items)}


def _when_text(days: int) -> str:
    if days <= 0:
        return "Bugun"
    if days == 1:
        return "Ertaga"
    return f"{days} kundan keyin"


def _celebration_alerts(db: Session, user, today) -> list:
    """Bayram bildirishnomalari: xodim tug'ilgan kuni va ish yubileyi,
    o'quvchi tug'ilgan kuni, rejadagi tadbirlar. Kim nimani ko'radi:
      - xodim sanalari — HR, filial rahbari, rahbariyat va event menejer;
      - o'quvchi tug'ilgan kunlari va tadbirlar — EVENTS_ACCESS
        (event menejer, HR, SMM, rahbariyat)."""
    see_staff = (user.role in tuple(roles.STAFF_DATES_ACCESS)
                 or user.role in tuple(roles.EVENTS_ACCESS))
    see_events = user.role in tuple(roles.EVENTS_ACCESS)
    rows = []

    if see_staff:
        for r in _staff_dates(db, user, days=roles.STAFF_DATE_LEAD_DAYS):
            bday = r["kind"] == "birthday"
            greet = (f"{r['full_name']}, tug'ilgan kuningiz muborak bo'lsin! "
                     "Jony Academy jamoasi sizga sog'lik, tinchlik va "
                     "ishingizda katta yutuqlar tilaydi." if bday else
                     f"{r['full_name']}, jamoamizda {r['years']} yil "
                     "bo'ldingiz! Mehnatingiz va sabringiz uchun rahmat — "
                     "shu muhitni siz ham qurdingiz.")
            what = ("tug'ilgan kuni" if bday
                    else f"ish yubileyi ({r['years']} yil)")
            rows.append((r["days_left"], {
                "icon": "cake" if bday else "medal",
                "text": f"{'🎂' if bday else '🎉'} {_when_text(r['days_left'])}: "
                        f"{r['full_name']} — {what}",
                "tone": "emerald" if r["today"] else "sky",
                "detail": {
                    "type": "birthday" if bday else "anniversary",
                    "title": r["kind_label"],
                    "full_name": r["full_name"],
                    "who_label": "Xodim",
                    "fields": [
                        ["Lavozimi", r["role_label"]],
                        ["Filiali", r["branch"] or "—"],
                        ["Sana", r["date_label"]],
                        ["Qachon", _when_text(r["days_left"])],
                        (["Yoshi", f"{r['years']} ga to'ladi"] if bday else
                         ["Ishga kirgan", roles.uz_date_full(
                             date.fromisoformat(r["source_date"]))]),
                        ["Ishlagan muddati", r.get("tenure") or "—"],
                        ["Telefon", r["phone"] or "—"],
                    ],
                    "phone": r["phone"],
                    "greeting": greet,
                    # Event menejer xodimlar ro'yxatiga kirmaydi —
                    # unga Tadbirlar, HR/rahbariyatga HR "Sanalar"
                    "link": "/events" if see_events else "/hr?tab=dates",
                    "link_label": ("Tadbirlar" if see_events
                                   else "HR — Sanalar"),
                },
            }))

    if see_events:
        groups = {g.id: g.name for g in
                  db.query(models.Group.id, models.Group.name).all()}
        branches = {b.id: b.name for b in
                    db.query(models.Branch.id, models.Branch.name).all()}
        can_card = user.role in tuple(roles.TEACHING_STAFF)
        sq = scope_to_branch(db.query(models.Student), models.Student, user)
        for s in sq.filter(models.Student.status.notin_(("archived", "left")),
                           models.Student.birth_date.isnot(None)).all():
            nxt = roles.next_occurrence(s.birth_date, today)
            if not nxt:
                continue
            left = (nxt - today).days
            if left > roles.ALERT_BIRTHDAY_DAYS:
                continue
            age = nxt.year - s.birth_date.year
            rows.append((left, {
                "icon": "cake",
                "text": f"🎂 {_when_text(left)}: {s.full_name} (o'quvchi) — "
                        f"tug'ilgan kuni, {age} yosh",
                "tone": "emerald" if left == 0 else "sky",
                "detail": {
                    "type": "birthday",
                    "title": "Tug'ilgan kun",
                    "full_name": s.full_name,
                    "who_label": "O'quvchi",
                    "fields": [
                        ["Guruhi", groups.get(s.group_id) or "—"],
                        ["Filiali", branches.get(s.branch_id) or "—"],
                        ["Sana", roles.uz_date_full(nxt)],
                        ["Qachon", _when_text(left)],
                        ["Yoshi", f"{age} ga to'ladi"],
                        ["Telefon", s.phone or "—"],
                        ["Ota-ona telefoni", getattr(s, "parent_phone", None)
                         or "—"],
                    ],
                    "phone": s.phone or getattr(s, "parent_phone", None),
                    "greeting": (f"{s.full_name}, tug'ilgan kuningiz muborak "
                                 "bo'lsin! Jony Academy jamoasi sizga "
                                 "bilim, sog'lik va katta yutuqlar tilaydi."),
                    # Event menejer/SMM o'quvchi kartasiga to'liq kira
                    # olmaydi (to'lovlar va h.k. yopiq) — ularga Tadbirlar
                    "link": (f"/students/{s.id}" if can_card
                             else "/events"),
                    "link_label": ("O'quvchi kartasi" if can_card
                                   else "Tadbirlar"),
                },
            }))
        eq = scope_to_branch(db.query(models.Event), models.Event, user)
        for e in eq.filter(
                models.Event.event_date >= today,
                models.Event.event_date
                <= today + timedelta(days=roles.ALERT_EVENT_DAYS),
                models.Event.status.notin_(("done", "cancelled"))).all():
            left = (e.event_date - today).days
            kind = roles.EVENT_KIND_LABELS.get(e.kind, e.kind)
            rows.append((left, {
                "icon": "party",
                "text": f"🎈 {_when_text(left)}: {e.title} ({kind})"
                        + (f", {e.start_time}" if e.start_time else ""),
                "tone": "amber",
                "detail": {
                    "type": "event",
                    "title": kind,
                    "full_name": e.title,
                    "who_label": "Tadbir",
                    "fields": [
                        ["Sana", roles.uz_date_full(e.event_date)],
                        ["Qachon", _when_text(left)],
                        ["Vaqti", e.start_time or "—"],
                        ["Joyi", e.place or "—"],
                        ["Filiali", e.branch.name if e.branch else
                         "Barcha filiallar"],
                        ["Kimlar uchun", e.audience or "—"],
                        ["Mas'ul", e.responsible.full_name
                         if e.responsible else "—"],
                        ["Holati", roles.EVENT_STATUS_LABELS.get(
                            e.status, e.status)],
                        ["Izoh", e.note or "—"],
                    ],
                    "phone": None,
                    "greeting": None,
                    "link": "/events",
                    "link_label": "Tadbirlar",
                },
            }))

    rows.sort(key=lambda x: (x[0], x[1]["text"]))
    out = [it for _, it in rows[:roles.ALERT_CELEBRATION_MAX]]
    if len(rows) > roles.ALERT_CELEBRATION_MAX:
        out.append({
            "icon": "cake",
            "text": f"...va yana {len(rows) - roles.ALERT_CELEBRATION_MAX} "
                    "ta tug'ilgan kun / tadbir",
            "link": "/events" if see_events else "/hr",
            "tone": "sky",
        })
    return out

