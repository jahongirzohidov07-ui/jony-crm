"""Auto-extracted from main.py during refactor (split-main). Domain: students."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import (APIRouter, Body, Depends, FastAPI, HTTPException,
                     Request)
from fastapi.responses import JSONResponse
from sqlalchemy import (delete as sa_delete, func, func as sa_func, or_,
                        select as sa_select, text, update as sa_update)
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
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()

@router.get("/api/students/{student_id}/lead")
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

@router.get("/api/students/{student_id}/exams")
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

@router.get("/api/students/{student_id}/attendance")
def student_attendance(
    student_id: int,
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, roles.HR_MANAGER)),
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
        "late": a.present == 2,
        "grade": grades.get(ls.id),
        "homework": a.homework,
        "homework_label": roles.HOMEWORK_LABELS.get(a.homework),
        "homework_tone": roles.HOMEWORK_TONE.get(a.homework),
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
        "homework": _homework_stats(db, student_id, since=start),
    }

@router.get("/api/students/{student_id}/attendance-grid")
def student_attendance_grid(
    student_id: int,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, roles.HR_MANAGER)),
):
    """O'quvchining OYLIK davomat panjarasi — guruh kesimida.

    2026-08-12, Jahongir: "davomat degan joyga bossa o'quvchi
    oynasidan chiqmagan holda oyna ochilsa va yoqlamalari korinib
    tursa, muzlatilganlarniki ham".

    Har bir guruh uchun o'sha oydagi DARS KUNLARI ustun bo'lib
    chiqadi: keldi / kelmadi / kechikdi / hali belgilanmagan, va
    o'sha kungi baho. O'quvchi holati (faol, muzlatilgan, arxiv)
    hech narsani yashirmaydi — tarix baribir ko'rinadi.
    """
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not _in_user_branches(db, user, st.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")

    today = roles.local_today()
    year = year or today.year
    month = month or today.month
    if not (1 <= month <= 12):
        raise HTTPException(400, "Oy 1-12 oralig'ida bo'lishi kerak")
    start, end = billing.month_bounds(year, month)

    # Shu oyda o'quvchi davomati BELGILANGAN barcha darslar (qaysi
    # guruhda bo'lishidan qat'i nazar — guruh almashgan bo'lsa
    # ikkalasi ham chiqadi).
    att_rows = (db.query(models.Attendance, models.Lesson)
                .join(models.Lesson,
                      models.Attendance.lesson_id == models.Lesson.id)
                .filter(models.Attendance.student_id == student_id,
                        models.Lesson.date >= start,
                        models.Lesson.date <= end).all())
    by_lesson = {ls.id: a for a, ls in att_rows}
    gids = {ls.group_id for _a, ls in att_rows}
    # Hozirgi guruhi — hali yoqlama qo'yilmagan darslar ham bo'sh
    # katak bo'lib ko'rinsin.
    if st.group_id:
        gids.add(st.group_id)
    if not gids:
        return {"year": year, "month": month, "groups": [],
                "student": st.full_name, "status": st.status}

    lessons = (db.query(models.Lesson)
               .filter(models.Lesson.group_id.in_(gids),
                       models.Lesson.date >= start,
                       models.Lesson.date <= end)
               .order_by(models.Lesson.date).all())
    grades = {g.lesson_id: g.score
              for g in db.query(models.DailyGrade).filter(
                  models.DailyGrade.student_id == student_id).all()}
    groups = {g.id: g for g in db.query(models.Group).filter(
        models.Group.id.in_(gids)).all()}

    out = []
    for gid in gids:
        g = groups.get(gid)
        rows = [ls for ls in lessons if ls.group_id == gid]
        days = []
        present = absent = late = unmarked = 0
        for ls in rows:
            a = by_lesson.get(ls.id)
            if a is None:
                state = "none"
                unmarked += 1
            elif a.present == 2:
                state = "late"
                late += 1
                present += 1
            elif a.present:
                state = "present"
                present += 1
            else:
                state = "absent"
                absent += 1
            days.append({
                "date": ls.date.isoformat(),
                "state": state,
                "grade": grades.get(ls.id),
                "homework": a.homework if a else None,
                "homework_label": (roles.HOMEWORK_LABELS.get(a.homework)
                                   if a else None),
            })
        marked = present + absent
        t = db.query(models.Teacher).get(g.teacher_id) if g and g.teacher_id \
            else None
        out.append({
            "group_id": gid,
            "group": g.name if g else f"#{gid}",
            "teacher": t.full_name if t else None,
            "current": bool(st.group_id == gid),
            "days": days,
            "present": present, "absent": absent, "late": late,
            "unmarked": unmarked,
            "percent": round(present / marked * 100) if marked else None,
        })
    out.sort(key=lambda x: (not x["current"], x["group"]))
    return {
        "year": year, "month": month,
        "student": st.full_name, "status": st.status,
        "groups": out,
    }

@router.get("/api/students/{student_id}/coins", response_model=List[schemas.CoinEntryOut])
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

@router.post("/api/students/{student_id}/coins", response_model=schemas.CoinEntryOut)
def add_manual_coins(
    student_id: int,
    payload: schemas.CoinManual,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Qo'lda coin berish yoki yechish (tanlov, tadbir, jarima va h.k.)."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
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

@router.put("/api/students/{student_id}/coins")
def set_coin_balance(
    student_id: int,
    payload: schemas.CoinSetIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_BALANCE_EDIT)),
):
    """COIN BALANSINI TO'G'RILASH — asoschi va FILIAL RAHBARI.

    2026-08-15, Jahongir: "faqatgina asoschida coinlarni
    tahrirlaydigan funksiya qoshib ber coin oldida bitta qalamcha
    bilan yetadi".
    2026-09-01, Jahongir: "filial rahbarlari balansni tahrirlash
    huquqi bormi yoq bolsa shu tahrirlash huquqi bolsin" — filial
    rahbari ham qo'shildi, lekin FAQAT O'Z FILIALI o'quvchisiga.

    Eski yozuvlar O'CHIRILMAYDI. Balans yozuvlar yig'indisidan
    chiqadi, shuning uchun to'g'rilash FARQ yozuvi bo'lib qo'shiladi:
    tarix ham buzilmaydi, "kim va nima uchun o'zgartirdi" ham
    ko'rinib turadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    # Filial rahbari o'z filialidan tashqariga chiqmaydi (pul
    # tahririda ham xuddi shu qoida — finance.edit_payment).
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    want = int(payload.balance)
    if want < 0:
        raise HTTPException(400, "Coin manfiy bo'lishi mumkin emas")
    now = _student_coin_balance(db, student_id)
    diff = want - now
    if diff == 0:
        return {"ok": True, "balance": now, "changed": 0,
                "message": "Balans allaqachon shunday"}
    reason = (payload.note or "").strip()
    entry = models.CoinEntry(
        student_id=student_id, amount=diff, source="admin_fix",
        note=(f"{roles.UZ_LABELS.get(user.role, user.role)} "
              f"to'g'riladi: {now} -> {want}"
              + (f". Sabab: {reason}" if reason else "")),
        created_by=user.full_name)
    db.add(entry)
    db.commit()
    audit.log(db, user, entity="student", action="coin_fix",
              entity_id=s.id, entity_label=s.full_name,
              field="coin", old_value=now, new_value=want,
              note=reason or None, branch_id=s.branch_id, commit=True)
    return {"ok": True, "balance": want, "changed": diff}


def sweep_left_to_archive(db: Session, branch_id: int | None = None) -> int:
    """GURUHSIZ VA QARZSIZ "Chiqib ketgan"larni AVTOMAT arxivga o'tkazish.

    2026-08-22, Jahongir: "guruhi yoq, qarzi yoq bo'lsa arxivga tushsin,
    chiqib ketgan joyi kerak emasda bizga".

    Ilgari arxivga o'tish faqat IKKI holatda ishlardi: guruhdan
    chiqarilayotgan payt (qarzi bo'lmasa) va qarzdor keyin to'lov
    qilganda. Ya'ni balans BOSHQA yo'l bilan nolga chiqsa (chegirma,
    to'lov tuzatish, avgust dubl yechimini tozalash kabi) — odam
    "Chiqib ketgan" bo'lib ro'yxatda osilib qolardi.

    Endi ro'yxat har ochilganda shu holat tekshiriladi. Shart qat'iy:
    holati "Chiqib ketgan" + asosiy guruhi yo'q + qarzi yo'q.
    Faol o'quvchi yoki qarzdor hech qachon tegilmaydi.
    """
    q = db.query(models.Student).filter(
        models.Student.status == roles.STUDENT_LEFT,
        models.Student.group_id.is_(None))
    if branch_id:
        q = q.filter(models.Student.branch_id == branch_id)
    cands = q.all()
    if not cands:
        return 0
    ids = [s.id for s in cands]

    # OCHIQ QOLGAN BOG'LANISHLAR (2026-08-22). Asosiy guruhi bo'sh, lekin
    # student_groups'dagi qatori hali "faol" turgan holatlar bor —
    # holat qo'lda "Chiqib ketgan"ga o'zgartirilganda bog'lanish
    # yopilmay qolgan. Kartada guruh ko'rinib turadi-yu, aslida u
    # hech qaysi guruhda o'qimaydi. Arxivga o'tkazayotib shu qator
    # ham yopiladi — ma'lumot izchil bo'lib qoladi.
    open_links: dict = {}
    for lnk in (db.query(models.StudentGroupLink)
                .filter(models.StudentGroupLink.student_id.in_(ids),
                        models.StudentGroupLink.active == 1).all()):
        open_links.setdefault(lnk.student_id, []).append(lnk)
    # Balanslar — bitta so'rovda (har biriga alohida so'rov yubormaymiz)
    sums = dict(db.query(models.Payment.student_id,
                         func.coalesce(func.sum(models.Payment.amount), 0))
                .filter(models.Payment.student_id.in_(ids))
                .group_by(models.Payment.student_id).all())

    moved = 0
    today = roles.local_today()
    for st in cands:
        if (sums.get(st.id) or 0) < -0.01:
            continue                      # qarzi bor — Qarzdorlarda qoladi
        for lnk in open_links.get(st.id, []):
            lnk.active = 0
            if not lnk.left_date:
                lnk.left_date = today
        st.status = "archived"
        st.archive_when_paid = 0
        _sync_student_left_date(st)
        audit.log(db, None, entity="student", action="auto_archive",
                  entity_id=st.id, entity_label=st.full_name, field="status",
                  old_value=roles.STUDENT_LEFT, new_value="archived",
                  note="Guruhsiz va qarzsiz — avtomat arxivga o'tdi",
                  branch_id=st.branch_id)
        moved += 1
    if moved:
        db.commit()
    return moved


@router.get("/api/students", response_model=List[schemas.StudentOut])
def list_students(
    q: Optional[str] = None,
    group_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    left: bool = False,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # O'QUVCHI VA OTA-ONA BU RO'YXATNI KO'RMAYDI (2026-09-06 auditi).
    # Ilgari bu yo'l faqat "kirgan bo'lsa bo'ldi" edi: o'quvchi o'z
    # tokeni bilan filialidagi barcha o'quvchi ismi, telefoni va
    # BALANSINI olishi mumkin edi. O'quvchi ilovasi bu yo'ldan
    # foydalanmaydi — u /api/student/* yo'llari bilan ishlaydi.
    if user.role in (roles.STUDENT, roles.PARENT):
        raise HTTPException(403, "Bu ro'yxat sizga ochiq emas")
    backfill_missing_ids(db, "student", models.Student)
    # Guruhsiz + qarzsiz "Chiqib ketgan"lar ro'yxatda osilib qolmasin
    try:
        sweep_left_to_archive(db)
    except Exception:
        db.rollback()
    # Faol bo'lmagan o'quvchi va ishdan ketgan xodim chegirmalari
    # o'z-o'zidan to'xtasin (2026-08-22)
    try:
        _expire_discounts(db)
    except Exception:
        db.rollback()
    query = scope_to_branch(db.query(models.Student), models.Student, user,
                            branch_id)
    if q:
        query = query.filter(models.Student.full_name.ilike(f"%{q}%"))
    if group_id and left:
        # GURUHDAN O'CHIRILGANLAR (2026-08-18, Jahongir: "guruhdan
        # ochirilgan talaba bu yerda turmasin... Pastda alohida
        # guruhdan ochirilganlar bolimi tursa osha yerdni bossagina
        # alohida chiqsin"). Bu ro'yxat FAQAT tugma bosilganda
        # so'raladi: shu guruhdan chiqarilgan (bog'lanishi yopilgan)
        # yoki shu guruhda turib arxivga o'tgan o'quvchilar.
        gone_ids = [sid for (sid,) in
                    db.query(models.StudentGroupLink.student_id)
                    .filter(models.StudentGroupLink.group_id == group_id,
                            models.StudentGroupLink.active == 0).all()]
        query = query.filter(
            models.Student.id.in_(gone_ids or [-1])
            | (in_group(group_id)
               & models.Student.status.in_(("archived", "left"))))
        # Hozir guruhda faol o'qiyotganlar bu ro'yxatga tushmasin
        # (chiqarilib keyin QAYTA qo'shilganlar bo'lishi mumkin)
        query = query.filter(
            models.Student.status.in_(("archived", "left"))
            | ~in_group(group_id))
    elif group_id:
        # Ikki guruhga qatnaydigan o'quvchi IKKALASIDA ham chiqsin
        # (2026-08-17) — ilgari faqat asosiy guruhida ko'rinardi.
        query = query.filter(in_group(group_id))
        # 2026-08-18: guruh ro'yxatida ARXIVDAGI/KETGAN o'quvchi
        # TURMAYDI — ular pastdagi "Guruhdan o'chirilganlar"da.
        # Aniq status so'ralgan bo'lsa (masalan arxiv sahifasi) —
        # aralashmaymiz.
        if not status_filter:
            query = query.filter(
                ~models.Student.status.in_(("archived", "left")))
    if status_filter:
        query = query.filter(models.Student.status == status_filter)

    # Ustoz faqat O'Z guruhlarining o'quvchilarini ko'radi va balans
    # unga umuman ko'rsatilmaydi: bolaga qarzdorligi orqali emas,
    # o'qishi orqali qaraydi. Pul masalasi — administrator ishi.
    own_only = user.role in tuple(roles.OWN_GROUPS_ONLY)
    if own_only:
        t = _teacher_of_user(db, user)
        gids = [g.id for g in _cabinet_groups(db, user, t)] if t else []
        query = query.filter(models.Student.group_id.in_(gids or [-1]))

    # TEZLIK (2026-08-15): guruh, filial va guruhning ustozi OLDINDAN
    # birga o'qiladi. Ilgari pydantic har o'quvchi uchun alohida
    # so'rov yuborardi (45 guruh + 18 ustoz + 3 filial = 66 ortiqcha
    # so'rov). Javob AYNAN o'sha — faqat o'qish usuli o'zgardi.
    from sqlalchemy.orm import selectinload as _sel
    students = (query
                .options(_sel(models.Student.branch),
                         _sel(models.Student.group)
                         .selectinload(models.Group.teacher),
                         _sel(models.Student.group)
                         .selectinload(models.Group.branch))
                .order_by(models.Student.full_name).all())
    # Rasmni lazy-load ham qilmaslik uchun instansiyaga None yozamiz
    # (ORM hodisalarini chetlab) - aks holda pydantic har o'quvchi
    # uchun alohida so'rov yuborardi (N+1 + trafik).
    for _s in students:
        _s.__dict__.setdefault("photo", None)
    # TEZLIK: balanslar bitta so'rovda (har o'quvchiga alohida so'rov —
    # N+1 — 2-3 ming o'quvchida sahifani sekinlashtirib yuborardi).
    balances = dict(
        db.query(models.Payment.student_id,
                 func.coalesce(func.sum(models.Payment.amount), 0.0))
        .group_by(models.Payment.student_id).all())
    rows = []
    for s in students:
        r = schemas.StudentOut.model_validate(s)
        r.balance = 0.0 if own_only else float(balances.get(s.id, 0) or 0)
        # TRAFIK (2026-08-12): ro'yxatda RASM yuborilmaydi. Har rasm
        # ~50KB data-URL, 2-3 ming o'quvchi = yuzlab MB bir ochilishda.
        # Aynan shu Neon'ning data-transfer kvotasini yeb, saytni
        # yotqizgan edi. Rasm faqat bitta o'quvchi ochilganda keladi.
        r.photo = None
        rows.append(r)
    return rows

@router.get("/api/students/{student_id}", response_model=schemas.StudentDetail)
def get_student(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    # O'quvchi faqat O'ZINING kartasini ko'radi (2026-09-06 auditi);
    # ota-ona umuman bu yo'ldan emas, maxsus havola bilan kiradi.
    if user.role == roles.PARENT:
        raise HTTPException(403, "Bu ma'lumot sizga ochiq emas")
    if user.role == roles.STUDENT:
        _me = (db.query(models.Student)
               .filter(models.Student.user_id == user.id).first())
        if not _me or _me.id != s.id:
            raise HTTPException(403, "Bu ma'lumot sizga ochiq emas")
    out = schemas.StudentDetail.model_validate(s)
    if user.role in tuple(roles.OWN_GROUPS_ONLY):
        # Ustozga: o'z o'quvchisi bo'lsagina, pulsiz
        if s.group_id:
            _get_group_in_scope(db, s.group_id, user)
        else:
            raise HTTPException(403, "Bu o'quvchi sizga biriktirilmagan")
        out.balance = 0.0
        out.payments = []
        return out
    # FILIAL AUDITI: filialga bog'langan xodim faqat o'z filialini ko'radi
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    out.balance = student_balance(db, s.id)
    # TARTIB: eng oxirgi to'lov/yechim eng tepada. Ilgari tartib
    # umuman berilmagan edi va baza qatorlarni o'zi xohlagancha
    # (odatda id bo'yicha) qaytarardi — LC UP importi eski to'lovlarni
    # oxirgi sanadan boshlab yozgani uchun bugungi to'lov ro'yxatning
    # ENG PASTIGA tushib qolardi (Jahongir, 2026-08-12: "nega tolov
    # avgust kiritilgani eng pastga tushib ketgan").
    _pays = sorted(s.payments,
                   key=lambda p: (p.created_at or datetime.min, p.id),
                   reverse=True)
    out.payments = [schemas.PaymentOut.model_validate(p) for p in _pays]
    return out

@router.post("/api/students", response_model=schemas.StudentOut)
def create_student(
    payload: schemas.StudentCreate,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    # DUBLIKAT TEKSHIRUVI.
    #
    # 2026-08-18, Jahongir: "qara shu boymirzayev Bekzod degan o'quvchi
    # yoqolib qolib bir paydo bolib qolyabdi, keyi yana men qoshib
    # qoydim deyabdi admin".
    #
    # Sabab topildi: o'quvchi 3 darsga ketma-ket kelmagani uchun
    # AVTOMUZLATILGAN edi (auto_freeze). Muzlatilgan o'quvchi faol
    # ro'yxatdan va davomat jadvalidan tushib qoladi — admin uni
    # topolmay YANGI karta ochib yuborgan. Natijada bitta bolaga
    # ikkita yozuv: biri muzlatilgan (qarzi/balansi bilan), ikkinchisi
    # bo'm-bo'sh yangi. Bu holat takrorlanaveradi.
    #
    # Shuning uchun tekshiruv ikki tomonlama qilindi:
    #   1) ISM bo'yicha — avvalgidek;
    #   2) TELEFON bo'yicha — YANGI. Ism biroz boshqacha yozilsa ham
    #      (masalan "Bekzod" va "Bekzodbek Ravshan o'g'li") raqam
    #      bir xil bo'lsa ushlanadi.
    # Ikkalasi ham ARXIV va MUZLATILGANLARNI ham qamrab oladi — aynan
    # o'shalar ko'rinmagani uchun dubl paydo bo'ladi. Ogohlantirishda
    # holati ham yoziladi, admin nima qilishni biladi: yangi karta
    # ochish emas, eskisini TIKLASH kerak.
    if not force:
        _ST_LABEL = {"active": "faol", "frozen": "MUZLATILGAN",
                     "archived": "ARXIVDA", "trial": "sinov darsida"}

        def _tail(v):
            d = "".join(ch for ch in str(v or "") if ch.isdigit())
            return d[-9:] if len(d) >= 9 else ""

        nm = " ".join((payload.full_name or "").split()).lower()
        ph = _tail(payload.phone)
        pph = _tail(getattr(payload, "parent_phone", None))
        same = None
        by_phone = False
        for st in db.query(models.Student).all():
            if " ".join((st.full_name or "").split()).lower() == nm \
                    and st.status != "archived":
                same = st
                break
            if same:
                continue
            s_ph, s_pph = _tail(st.phone), _tail(st.parent_phone)
            # DIQQAT: ota-ona raqami ↔ ota-ona raqami solishtirilmaydi.
            # Aka-uka, opa-singil bir xil ota-ona raqamini yozadi
            # (masalan Murotova Dilshoda va Murodova Durdona) — ular
            # dublikat emas, ularni to'sish noto'g'ri bo'lardi.
            hit = (
                (ph and (ph == s_ph or ph == s_pph))
                or (pph and pph == s_ph)
            )
            if hit:
                same, by_phone = st, True
        if same:
            g = db.query(models.Group).get(same.group_id) \
                if same.group_id else None
            joy = f", {g.name} guruhida" if g else ""
            holat = _ST_LABEL.get(same.status, same.status or "")
            qaysi = "Bu TELEFON RAQAM" if by_phone else "Bunday ISMLI"
            kengash = ""
            if same.status == "frozen":
                kengash = (" U 3 darsga ketma-ket kelmagani uchun "
                           "avtomuzlatilgan bo'lishi mumkin — shuning "
                           "uchun ro'yxatda ko'rinmayapti. Yangi karta "
                           "ochmang, o'sha kartani TIKLANG: qarzi, "
                           "to'lov tarixi va davomati o'sha yerda.")
            elif same.status == "archived":
                kengash = (" U arxivda turibdi. Yangi karta ochmang — "
                           "arxivdan tiklang, tarixi saqlanib qoladi.")
            raise HTTPException(
                409,
                f"{qaysi} bilan o'quvchi allaqachon bor: "
                f"{same.full_name} (#{same.id}, {holat}{joy})."
                f"{kengash} Agar bu haqiqatan BOSHQA odam bo'lsa — "
                "tasdiqlang.")
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
    # AVTOMAT KIRISH HISOBI (2026-08-10, Jahongir so'radi): o'quvchi
    # kiritilishi bilan unga hisob ochiladi — login telefon raqami,
    # parol jonyjony. Alohida "hisob ochish" bosqichi qolmadi.
    # Ota-onaga esa hisob umuman ochilmaydi: u maxsus havola
    # (parent_token) orqali kiradi, u ham shu yerda avtomat turadi.
    _ensure_student_account(db, s)
    # Guruh bog'lanishi (2026-08-17) — yangi o'quvchi ham darrov
    # bog'lanish jadvaliga tushsin, ikki guruhli bo'lishi mumkin.
    if s.group_id:
        try:
            attach_group(db, s, s.group_id, user, joined=s.enrolled_date)
            db.commit()
        except Exception:
            db.rollback()
    db.refresh(s)
    return to_student_out(db, s)

def _transfer_recharge(db: Session, s: models.Student,
                       old_g, new_g, user, today=None) -> int:
    """Guruh almashtirishda JORIY OY to'lovini taqsimlash (Jahongir):
    "birinchi 6 ta dars oqigan to'lov summasi yechib olib
    hisoblansinda, qolgan summa yangi o'tgan guruh uchun".

    Eski guruh(lar)da shu oy YO'QLAMASI BELGILANGAN darslar o'sha
    guruh narxida, yangi guruhda bugundan oy oxirigacha qolgan
    darslar yangi narxda. Mavjud oylik hisob (charge) shu taqsimotga
    almashtiriladi; hali hisoblanmagan bo'lsa - darhol yoziladi
    (keyin oylik hisob-kitob uni takrorlamaydi, period belgisi bor).

    Qaytaradi: eski guruhdagi belgilangan yo'qlamalar soni."""
    today = today or roles.local_today()
    period = f"{today.year:04d}-{today.month:02d}"
    month_start = date(today.year, today.month, 1)

    # Shu oy BELGILANGAN yo'qlamalari - guruhlar kesimida (bir oyda
    # ikki marta ko'chsa ham har guruhdagisi o'z narxida hisoblanadi)
    rows = (db.query(models.Lesson.group_id,
                     func.count(models.Attendance.id))
            .join(models.Attendance,
                  models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == s.id,
                    models.Lesson.date >= month_start,
                    models.Lesson.date <= today,
                    models.Lesson.group_id != new_g.id)
            .group_by(models.Lesson.group_id).all())
    old_attended = 0
    old_sum = 0.0
    gnames = {g.id: g for g in db.query(models.Group).filter(
        models.Group.id.in_([gid for gid, _ in rows] or [-1])).all()}
    parts = []
    for gid, cnt in rows:
        g = gnames.get(gid)
        price = (g.lesson_price or 0) if g else 0
        old_sum += cnt * price
        old_attended += cnt
        if g:
            parts.append(f"{g.name}da {cnt} dars")

    left = _lessons_left_in_month(db, new_g.id, today)
    new_cnt = len(left)
    new_sum = new_cnt * (new_g.lesson_price or 0)
    parts.append(f"{new_g.name}da {new_cnt} dars")

    disc = _student_discount_percent(db, s)
    total = roles.money((old_sum + new_sum) * (100 - disc) / 100)
    note = ("Guruh almashtirildi: " + " + ".join(parts)
            + (f" (chegirma {disc}%)" if disc else ""))

    charge = (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.period == period,
                      models.Payment.kind == "charge").first())
    if charge is not None:
        old_amt = charge.amount
        charge.amount = -abs(total)
        charge.note = note
        audit.log(db, user, entity="payment", action="update",
                  entity_id=charge.id, entity_label=s.full_name,
                  field="Oylik hisob (guruh almashtirildi)",
                  old_value=old_amt, new_value=charge.amount, note=note,
                  branch_id=s.branch_id)
    elif total > 0 and not _charge_skipped(db, s.id, period):
        p = models.Payment(student_id=s.id, amount=-abs(total),
                           kind="charge", period=period, note=note,
                           created_by=user.full_name)
        db.add(p)
        audit.log(db, user, entity="payment", action="create",
                  entity_label=s.full_name,
                  field="Oylik hisob (guruh almashtirildi)",
                  new_value=p.amount, note=note, branch_id=s.branch_id)
    return old_attended


@router.put("/api/students/{student_id}", response_model=schemas.StudentOut)
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
    # Filialga bog'langan xodim boshqa filial o'quvchisini tahrirlamaydi
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    changes = payload.model_dump(exclude_unset=True)

    # GURUHSIZ O'QUVCHI "FAOL" BO'LA OLMAYDI (2026-08-15, Jahongir:
    # "birorta oquvchi guruhsiz lekin faol bola olmaydi guruhdan
    # chiqarildimi u faol emas endi"). Guruhi bo'lmagan odam uchun
    # dars ham, hisob ham yo'q — u "Chiqib ketgan" yoki arxivda
    # bo'lishi kerak.
    _new_group = changes.get("group_id", s.group_id)
    if changes.get("status") == "active" and not _new_group:
        # Ataylab "faol" qilinmoqchi, lekin guruhi yo'q — to'sib
        # qo'yamiz va nima qilish kerakligini aytamiz.
        raise HTTPException(
            400, "Guruhsiz o'quvchi \"Faol\" bo'la olmaydi. Avval "
                 "guruhga qo'shing yoki holatini \"Chiqib ketgan\" "
                 "deb qoldiring.")
    if ("group_id" in changes and not changes["group_id"]
            and changes.get("status", s.status) == "active"):
        # Guruhdan olindi — holat o'zi "Chiqib ketgan"ga o'tadi
        changes["status"] = roles.STUDENT_LEFT

    # Parallel tahrir himoyasi: men ochgan versiyadan keyin boshqa
    # xodim o'zgartirgan bo'lsa — ustidan yozmaymiz.
    expected = changes.pop("expected_updated_at", None)
    if expected is not None:
        server_v = s.updated_at.isoformat() if s.updated_at else ""
        if server_v != expected:
            raise HTTPException(
                409, "Bu kartani shu orada boshqa xodim o'zgartirdi. "
                     "Sahifani yangilab, qaytadan urinib ko'ring.")

    # Yangi guruhga o'tkazilyaptimi - sig'im va daraja tekshiriladi.
    new_gid = changes.get("group_id")
    _old_group = None
    _new_group = None
    if new_gid and new_gid != s.group_id:
        g = db.query(models.Group).get(new_gid)
        _raise_if_blocked(_check_enrolment(db, s, g), force=force)
        _old_group = s.group
        _new_group = g
        # O'quvchining darajasi hali yo'q bo'lsa - guruhnikidan olamiz.
        if g and not s.level:
            changes.setdefault("subject", g.subject)
            changes.setdefault("level", g.level)
    # Eski qiymatlar hali joyida turganda yozib olamiz.
    audit.log_changes(db, user, entity="student", obj=s, changes=changes)
    _prev_gid = s.group_id
    for k, v in changes.items():
        setattr(s, k, v)
    s.updated_at = datetime.utcnow()
    _sync_student_left_date(s)
    # GURUH BOG'LANISHI (2026-08-17). Kartadagi "guruh" maydoni
    # o'zgarsa bog'lanish jadvali ham yursin — aks holda o'quvchi
    # yangi guruhda ko'rinmay qolardi. Ko'p guruhli o'quvchida bu
    # maydon ASOSIY guruhni almashtiradi, qolganlariga tegmaydi.
    if "group_id" in changes and s.group_id != _prev_gid:
        # DIQQAT: avval YANGISINI qo'shamiz, keyin eskisini yopamiz.
        # Teskarisi qilinsa detach_group() asosiy guruhni bo'shatib
        # yuboradi va s.group_id None bo'lib qoladi.
        _target = s.group_id
        try:
            if _target:
                attach_group(db, s, _target, user)
            if _prev_gid and _prev_gid != _target:
                detach_group(db, s, _prev_gid)
            s.group_id = _target
        except Exception:
            db.rollback()
    db.commit()

    # GURUH ALMASHTIRILDI (Jahongir, 2026-08-11): eski ustozning
    # yo'qlamalari o'z joyida qoladi (oyligi saqlanadi), joriy oy
    # to'lovi taqsimlanadi, tarixga "Guruh almashtirildi" yoziladi.
    if _new_group is not None:
        try:
            _att = _transfer_recharge(db, s, _old_group, _new_group, user)
            audit.log(db, user, entity="student", action="group_move",
                      entity_id=s.id, entity_label=s.full_name,
                      old_value=_old_group.name if _old_group else None,
                      new_value=_new_group.name,
                      note=(f"{_att} ta belgilangan yo'qlama bilan "
                            "ko'chdi - eski yo'qlamalari avvalgi "
                            "ustoz oyligida qoladi"),
                      branch_id=s.branch_id)
            db.commit()
        except Exception:
            db.rollback()

    # Hisobi hali yo'q bo'lsa (masalan avval telefon kiritilmagan
    # edi) — endi ochib qo'yamiz. Hisobi bori qayta ochilmaydi.
    _ensure_student_account(db, s)
    db.refresh(s)
    return to_student_out(db, s)

# =====================================================================
#  IKKI YOZUVNI BIRLASHTIRISH (2026-08-17)
#
#  Jahongir: "qara sen aytyabman shu ikktani bitta qil, bittasini
#  toliq ochirib tashla, davomatri, otsin lekin bunga".
#
#  Kelib chiqishi: bazada bitta o'quvchida bitta guruh bo'lgani uchun
#  ikki fanga qatnaydigan bola IKKI MARTA kiritilgan. Endi ko'p guruh
#  bor, shuning uchun ikkitasini bittaga yig'ish kerak.
#
#  QOIDA: hech narsa YO'QOLMAYDI. Ortiqcha yozuvning BUTUN tarixi —
#  davomat, baho, imtihon, coin, XP, to'lov, chegirma, shartnoma,
#  shikoyat — omon qolgan kartaga KO'CHADI. Ko'chirilgach ortiqcha
#  yozuv bo'm-bo'sh qobiq bo'lib qoladi va o'sha holda o'chiriladi.
#  Ya'ni "o'chirish" hech qanday ma'lumotni yo'qotmaydi.
# =====================================================================

# Bog'langan jadvallar QO'LDA sanalmaydi — SQLAlchemy metadata'sidan
# avtomat topiladi (2026-08-17). Ilgari qo'lda ro'yxat bor edi va
# xp_streak_milestones o'tkazib yuborilgan — birlashtirish server
# xatosi bergan. Endi yangi jadval qo'shilsa ham o'zi topiladi.

def _student_fk_columns():
    """students.id ga bog'langan (jadval, ustun) juftliklari."""
    out = []
    for mapper in models.Base.registry.mappers:
        cls = mapper.class_
        if cls is models.Student:
            continue
        for col in mapper.local_table.columns:
            for fk in col.foreign_keys:
                if fk.target_fullname == "students.id":
                    out.append((cls, col.name))
    return out


# Bitta o'quvchida BITTA bo'lishi kerak — ko'chirilsa ikkita bo'lib
# qoladi yoki unique cheklovga urinadi. Ular ko'chirilmaydi:
# omon qolganda bori qoladi, ortiqchasi o'chiriladi.
# DIQQAT: bu yerga faqat HAQIQATAN bitta bo'lishi kerak bo'lgan
# jadval yoziladi. Masalan XpStreakMilestone bunday EMAS — bola 7
# kunlik ham, 14 kunlik ham nishon olishi mumkin, ikkalasi ham
# saqlanishi kerak (test tutdi).
_MERGE_SINGLETON = {"StudentGamification", "XpStreak",
                    "StudentGroupLink"}

# Ko'chgandan keyin TAKRORI olib tashlanadigan jadvallar: bazada
# unique cheklov yo'q, lekin mazmunan bir xil yozuv ikki marta
# turmasligi kerak (masalan "7 kunlik nishon" ikkita bo'lmasin).
_MERGE_DEDUPE = {
    "XpStreakMilestone": ("kind", "milestone"),
    "StudentAchievement": ("achievement_id",),
    "VocabUnitPass": ("unit", "language"),
}


def _dedupe_after_merge(db: Session, keep_id: int) -> dict:
    """Bir xil yozuv ikki marta qolib ketmasin."""
    out = {}
    for name, keys in _MERGE_DEDUPE.items():
        M = getattr(models, name, None)
        if M is None or not hasattr(M, "student_id"):
            continue
        cols = [getattr(M, k, None) for k in keys]
        if any(c is None for c in cols):
            continue
        seen, gone = set(), 0
        for r in (db.query(M).filter(M.student_id == keep_id)
                  .order_by(M.id).all()):
            sig = tuple(getattr(r, k) for k in keys)
            if sig in seen:
                db.delete(r)
                gone += 1
            else:
                seen.add(sig)
        if gone:
            out[f"{name} (takror)"] = gone
    return out


@router.post("/api/students/{keep_id}/merge/{drop_id}")
def merge_students(
    keep_id: int,
    drop_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """Ikki yozuvni bitta qilish. FAQAT ASOSCHI.

    keep_id — qoladigan karta, drop_id — yo'q qilinadigani."""
    if keep_id == drop_id:
        raise HTTPException(400, "Bir xil yozuv")
    keep = db.query(models.Student).get(keep_id)
    drop = db.query(models.Student).get(drop_id)
    if not keep or not drop:
        raise HTTPException(404, "O'quvchi topilmadi")

    # XAVFSIZLIK: tasodifan boshqa odamni qo'shib yubormaslik uchun
    # telefon yoki ism mos kelishi SHART.
    def dig(v):
        return "".join(ch for ch in (v or "") if ch.isdigit())[-9:]

    same_phone = dig(keep.phone) and dig(keep.phone) == dig(drop.phone)
    same_name = (keep.full_name or "").strip().lower() == \
        (drop.full_name or "").strip().lower()
    if not (same_phone or same_name):
        raise HTTPException(
            400, "Bu ikkisi bir odamga o'xshamayapti (telefon ham, ism "
                 "ham boshqa). Birlashtirish to'xtatildi.")

    moved = {}

    # 0) Ikkalasining ham bog'lanishi borligiga ishonch hosil qilamiz.
    #    Eski o'quvchilarda bog'lanish kunlik cron'da yaratiladi —
    #    u ishlamagan bo'lsa guruhlar ko'chmay qolardi (test tutdi).
    ensure_link(db, keep)
    ensure_link(db, drop)
    db.flush()

    # 1) GURUHLAR — ortiqchaning guruhlari omon qolganga o'tadi
    for lk in (db.query(models.StudentGroupLink)
               .filter(models.StudentGroupLink.student_id == drop.id,
                       models.StudentGroupLink.active == 1).all()):
        try:
            attach_group(db, keep, lk.group_id, user,
                         joined=lk.joined_date)
        except Exception:
            db.rollback()
    db.query(models.StudentGroupLink).filter(
        models.StudentGroupLink.student_id == drop.id).delete(
            synchronize_session=False)

    # 2) DAVOMAT — bir darsda ikki yozuv bo'lib qolmasin
    keep_lessons = {lid for (lid,) in db.query(models.Attendance.lesson_id)
                    .filter(models.Attendance.student_id == keep.id).all()}
    n_att = n_dup = 0
    for a in (db.query(models.Attendance)
              .filter(models.Attendance.student_id == drop.id).all()):
        if a.lesson_id in keep_lessons:
            db.delete(a)          # o'sha darsda allaqachon yozuv bor
            n_dup += 1
        else:
            a.student_id = keep.id
            n_att += 1
    if n_att:
        moved["Davomat"] = n_att
    if n_dup:
        moved["Davomat (takror, olib tashlandi)"] = n_dup

    # 3) QOLGAN HAMMA JADVAL — metadata'dan avtomat
    for M, colname in _student_fk_columns():
        name = M.__name__
        if name == "Attendance" and colname == "student_id":
            continue                     # yuqorida alohida ishlandi
        col = getattr(M, colname)
        if name in _MERGE_SINGLETON:
            # Bittalik: omon qolganda bori qolsin, ortiqchasi o'chsin
            has = db.query(M).filter(col == keep.id).first()
            gone = 0
            for r in db.query(M).filter(col == drop.id).all():
                if has:
                    db.delete(r)
                    gone += 1
                else:
                    setattr(r, colname, keep.id)
                    has = r
            if gone:
                moved[f"{name} (takror)"] = gone
            continue
        # Ko'chirishda unique cheklovga urilishi mumkin — o'sha
        # yozuvni o'tkazib yuboramiz, qolgani ko'chaveradi.
        sp = db.begin_nested()
        try:
            n = (db.query(M).filter(col == drop.id)
                 .update({col: keep.id}, synchronize_session=False))
            sp.commit()
            if n:
                moved[name] = n
        except Exception:
            sp.rollback()
            ok = skip = 0
            for r in db.query(M).filter(col == drop.id).all():
                sp2 = db.begin_nested()
                try:
                    setattr(r, colname, keep.id)
                    db.flush()
                    sp2.commit()
                    ok += 1
                except Exception:
                    sp2.rollback()
                    db.delete(r)
                    skip += 1
            if ok:
                moved[name] = ok
            if skip:
                moved[f"{name} (takror)"] = skip

    # 5) Bo'sh maydonlarni to'ldiramiz (ma'lumot boy bo'lsin)
    for f in ("phone", "parent_phone", "birth_date", "address", "school",
              "school_grade", "photo", "middle_name", "note"):
        if not getattr(keep, f, None) and getattr(drop, f, None):
            setattr(keep, f, getattr(drop, f))
    if drop.enrolled_date and (not keep.enrolled_date
                               or drop.enrolled_date < keep.enrolled_date):
        keep.enrolled_date = drop.enrolled_date

    # 6) Login: ortiqchasidagi hisob bo'shatiladi (bitta odam — bitta login)
    old_user_id = drop.user_id
    drop.user_id = None
    db.flush()
    if old_user_id and not keep.user_id:
        keep.user_id = old_user_id
    elif old_user_id:
        u = db.query(models.User).get(old_user_id)
        if u:
            u.is_active = 0     # ikkinchi login o'chiriladi

    # Takror yozuvlarni tozalaymiz (7 kunlik nishon ikkita bo'lmasin)
    try:
        moved.update(_dedupe_after_merge(db, keep.id))
    except Exception:
        pass

    drop_name = drop.full_name
    drop_public = drop.public_id
    db.flush()
    db.delete(drop)             # endi bo'm-bo'sh qobiq
    sync_primary_group(db, keep)
    db.commit()
    db.refresh(keep)

    audit.log(db, user, entity="student", action="update",
              entity_id=keep.id, entity_label=keep.full_name,
              field="Ikki yozuv birlashtirildi",
              old_value=f"{drop_name} ({drop_public or drop_id})",
              new_value="; ".join(f"{k}: {v}" for k, v in moved.items())
                        or "ko'chirilgan yozuv yo'q",
              branch_id=keep.branch_id, commit=True)

    return {"ok": True, "kept": keep.id, "removed": drop_id,
            "moved": moved,
            "balance": student_balance(db, keep.id),
            "groups": len(student_group_ids(db, keep.id))}


# O'quvchi o'chirilganda TEGILMAYDIGAN jadvallar. payments_deleted —
# o'chirilgan to'lovlar arxivi: pul tarixi hech qachon yo'qolmasligi
# kerak (ichida o'quvchining ismi ham saqlanadi, ya'ni yetim qolmaydi).
_PURGE_KEEP_TABLES = {"payments_deleted", "audit_logs"}


def _purge_student_children(db: Session, sid: int) -> dict:
    """O'quvchiga bog'langan barcha yozuvlarni tozalash.

    2026-08-22: arxivdan o'chirish 500 xato berardi —
    "debtor_contacts_student_id_fkey violates". O'quvchiga 40 dan ortiq
    jadval bog'langan (to'lov, yo'qlama, coin, imtihon, XP, sertifikat,
    qarz aloqasi...), ularning hammasi tozalanmaguncha baza qatorni
    o'chirishga ruxsat bermaydi.

    Qoida oddiy: ustun nomi "student_id" bo'lsa — bu yozuv o'sha
    o'quvchiniki, o'chiriladi. Boshqa nomdagi havola (masalan lidning
    converted_student_id yoki chegirmadagi referrer_student_id) —
    boshqa birovning yozuvi, u YO'QOTILMAYDI, faqat havola bo'shatiladi.
    """
    removed: dict = {}
    for table in reversed(models.Base.metadata.sorted_tables):
        if table.name in ("students",) or table.name in _PURGE_KEEP_TABLES:
            continue
        for col in table.columns:
            points_to_student = any(
                fk.column.table.name == "students" for fk in col.foreign_keys)
            if col.name == "student_id":
                pass                      # o'ziniki — o'chiriladi
            elif points_to_student:
                # begona yozuvdagi havola — faqat bo'shatiladi
                db.execute(sa_update(table).where(col == sid)
                           .values({col.name: None}))
                continue
            else:
                continue
            r = db.execute(sa_delete(table).where(col == sid))
            if r.rowcount:
                removed[table.name] = r.rowcount
    return removed


@router.delete("/api/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    # 2026-08-18, Jahongir: "arxivdagilarni ochirishni faqatgina menga
    # asoschiga ruxsatini ber". O'quvchini BUTUNLAY o'chirish — tarixi
    # bilan yo'qotadigan amal, endi faqat asoschi qila oladi. Qolganlar
    # arxivga o'tkazadi (hech narsa yo'qolmaydi).
    user=Depends(require_role(roles.FOUNDER)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    name, bid = s.full_name, s.branch_id
    removed = _purge_student_children(db, s.id)
    db.delete(s)
    # Auditga NIMA o'chirilgani ham yoziladi: keyin "bu odamning
    # to'lovlari qani" degan savol chiqsa, javob shu yerda turadi.
    detail = ", ".join(f"{k}:{v}" for k, v in sorted(removed.items())) or "—"
    audit.log(db, user, entity="student", action="delete", entity_id=student_id,
              entity_label=name, branch_id=bid,
              old_value=f"{name} (bog'liq yozuvlar: {detail})")
    db.commit()
    return {"ok": True, "removed": removed}

@router.get("/api/students/{student_id}/payments", response_model=List[schemas.PaymentOut])
def list_payments(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    # FILIAL AUDITI: pul tarixi — eng nozik ma'lumot. Ustozga umuman
    # ko'rinmaydi, filialga bog'langan xodimga faqat o'z filiali.
    if user.role in tuple(roles.OWN_GROUPS_ONLY) or \
            user.role in (roles.STUDENT, roles.PARENT):
        raise HTTPException(403, "To'lov tarixi sizga ochiq emas")
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    return (
        db.query(models.Payment)
        .filter(models.Payment.student_id == student_id)
        .order_by(models.Payment.created_at.desc(),
                  models.Payment.id.desc())
        .all()
    )

def _pay_coin(db: Session, s: models.Student,
              payment: models.Payment, today=None) -> None:
    """To'lov sanasiga qarab avtomat coin (Jahongir qoidasi):
    1-5 sana +10, 6-10 sana +5, 11-15 sana +1, 16-oy oxiri 0;
    oldingi oydan QARZ bilan kelib to'lasa (oydan o'tib) -5.

    Oyiga BIR marta: bo'lib-bo'lib to'laganda faqat birinchisiga.
    To'lov o'chirilsa coin ham qaytariladi (finance.delete_payment).
    Eski tizim ham xuddi shu qoidada qo'lda berardi - endi avtomat."""
    if today is None:
        today = roles.local_today()
    # Shu kalendar oyda allaqachon baholanganmi
    month_start = datetime(today.year, today.month, 1)
    if (db.query(models.CoinEntry)
            .filter(models.CoinEntry.student_id == s.id,
                    models.CoinEntry.source == "pay_ontime",
                    models.CoinEntry.created_at >= month_start).first()):
        return
    # Oldingi oylardan qarz: joriy oy avto-hisobini (charge, period=shu
    # oy) chiqarib tashlaganda balans manfiy bo'lsa - o'tgan oy puli
    # hali yopilmagan holda oy o'tib ketgan.
    period = f"{today.year:04d}-{today.month:02d}"
    bal = 0.0
    for p in (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.id != payment.id).all()):
        if p.kind == "charge" and p.period == period:
            continue
        bal += p.amount or 0
    if bal < -0.5:
        amount, note = -5, "To'lov oydan o'tib qilindi (-5 coin)"
    else:
        d = today.day
        if d <= 5:
            amount, note = 10, "To'lovni 5-sanagacha qildi (+10 coin)"
        elif d <= 10:
            amount, note = 5, "To'lovni 10-sanagacha qildi (+5 coin)"
        elif d <= 15:
            amount, note = 1, "To'lovni 15-sanagacha qildi (+1 coin)"
        else:
            return
    db.add(models.CoinEntry(
        student_id=s.id, amount=amount, source="pay_ontime",
        ref_id=payment.id, note=note, created_by="Avtomat"))


@router.post("/api/students/{student_id}/payments", response_model=schemas.PaymentOut)
def add_payment(
    student_id: int,
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASH_ACCESS)),
):
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")

    # ---------------------------------------------------------------
    #  DUBL TO'LOVGA QARSHI HIMOYA (2026-08-14, Jahongir: "Tugma ikki
    #  marta bosilsa yoki internet uzilib qayta yuborilsa — ikkita
    #  to'lov tushadi. Avgustdagi 480 000 so'mlik dubl aynan shu
    #  turdagi xato edi").
    #
    #  Ikki qatlam:
    #   1) IDEMPOTENTLIK KALITI — brauzer forma uchun bitta tasodifiy
    #      kalit yuboradi. Ayni kalit ikkinchi marta kelsa yangi yozuv
    #      OCHILMAYDI, birinchisining o'zi qaytariladi. Bu tarmoq
    #      uzilib qayta yuborilgan so'rovni ham to'liq to'sadi.
    #   2) 2 DAQIQALIK OGOHLANTIRISH — bir xil o'quvchiga bir xil
    #      summa 2 daqiqa ichida ikkinchi marta kiritilayotgan bo'lsa
    #      (masalan ikki xodim bir vaqtda kiritdi) — server to'xtatib
    #      so'raydi. Xodim "ha, bu haqiqatan boshqa to'lov" desa,
    #      forma force=true bilan qayta yuboriladi va o'tadi.
    # ---------------------------------------------------------------
    ckey = (payload.client_key or "").strip()[:64] or None
    if ckey:
        was = (db.query(models.Payment)
               .filter(models.Payment.client_key == ckey).first())
        if was:
            # Xuddi shu so'rov allaqachon bajarilgan — takror emas.
            # Javob birinchi yozuvning o'zi: brauzer uchun hech narsa
            # o'zgarmaydi, lekin bazada ikkinchi to'lov paydo bo'lmaydi.
            return was

    # Pul har doim butun so'm — kasr qoldiqlari yig'ilib ketmasin
    amount = roles.money(payload.amount)
    # 0 so'mlik yozuv (2026-09-06 audit): hisobga hech narsa qo'shmaydi,
    # lekin "yangi mijoz" statistikasini buzadi va ro'yxatni chalg'itadi.
    if not amount:
        raise HTTPException(400, "Summani kiriting — 0 so'mlik yozuv "
                                 "saqlanmaydi")
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

    # ESKI SANA bilan kiritish. 2026-08-12, Jahongir: "asoschiga va
    # moliyachiga eski sana bilan to'lov kirgizish funksiyasi
    # qoshilsin". Boshqa xodimlarga berilmaydi: kassa tarixini
    # orqaga surish - hisobotni buzadigan amal, shuning uchun u
    # faqat ikki lavozimda va auditda izi qoladi.
    when = None
    if payload.date:
        if user.role not in (roles.FOUNDER, roles.FINANCE_DIRECTOR):
            raise HTTPException(
                403, "O'tgan sana bilan to'lov kiritishni faqat asoschi "
                     "va moliya direktori qila oladi")
        if payload.date > roles.local_today():
            raise HTTPException(400, "Kelajak sanasi bilan bo'lmaydi")
        # Sana bo'yicha tartib to'g'ri chiqishi uchun kun ichidagi
        # vaqtni ham saqlaymiz (o'sha kunning hozirgi soati).
        _now = datetime.utcnow()
        when = datetime(payload.date.year, payload.date.month,
                        payload.date.day, _now.hour, _now.minute,
                        _now.second)

    # 2-qatlam: yaqinda AYNI SHUNDAY yozuv kiritilganmi?
    if not payload.force and payload.kind == "payment":
        since = datetime.utcnow() - timedelta(minutes=2)
        twin = (db.query(models.Payment)
                .filter(models.Payment.student_id == student_id,
                        models.Payment.kind == "payment",
                        models.Payment.amount == amount,
                        models.Payment.entered_at.isnot(None),
                        models.Payment.entered_at >= since)
                .order_by(models.Payment.id.desc()).first())
        if twin:
            raise HTTPException(409, detail={
                "message": (
                    f"Diqqat: {s.full_name} uchun {abs(amount):,.0f}"
                    .replace(",", " ") + " so'm to'lov hozirgina "
                    f"({twin.created_by or 'nomalum'}) kiritilgan. "
                    "Bu ikkinchi, boshqa to'lovmi?"),
                "problems": [{
                    "key": "duplicate_payment",
                    "label": "Takroriy to'lov",
                    "severity": "block",
                    "message": ("Agar bu xato bo'lsa — Bekor qiling. "
                                "Agar haqiqatan ikkinchi to'lov bo'lsa "
                                "— Baribir kiritish tugmasini bosing."),
                }],
                "can_force": True,
            })

    payment = models.Payment(
        student_id=student_id,
        amount=amount,
        kind=payload.kind,
        method=method,
        note=payload.note,
        created_by=user.full_name,
        client_key=ckey,
    )
    # Rostakam kiritilish vaqti — HAR DOIM server soati (eski sana
    # bilan kiritilsa ham). "Kim va qachon kiritdi" savoli javobsiz
    # qolmasin.
    payment.entered_at = datetime.utcnow()
    if when:
        payment.created_at = when
    db.add(payment)
    db.commit()
    db.refresh(payment)
    _ensure_public_id(db, "payment", payment)

    # Chegirma alohida amal sifatida yoziladi - "kim chegirma berdi"
    # degan savolga javob shu yerdan chiqadi.
    act = "discount" if payload.kind == "discount" else "create"
    _note = payload.note
    if when:
        _note = ((_note + " · ") if _note else "") + \
            f"ESKI SANA bilan kiritildi: {payload.date.isoformat()}"
    audit.log(db, user, entity="payment", action=act, entity_id=payment.id,
              entity_label=s.full_name, field=payload.kind,
              new_value=amount, note=_note, branch_id=s.branch_id)
    db.commit()

    # AVTOMAT COIN: to'lov sanasiga qarab (5-sanagacha +10, 10 gacha
    # +5, 15 gacha +1; oydan o'tib kelgan qarz uchun -5).
    if payload.kind == "payment" and amount > 0:
        try:
            _pay_coin(db, s, payment)
            db.commit()
        except Exception:
            db.rollback()

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

    # AVTOMAT ARXIV: guruhdan qarzdorligicha chiqarilgan o'quvchi
    # qarzini to'liq yopgach o'zi arxivga o'tadi.
    if payload.kind == "payment" and getattr(s, "archive_when_paid", 0) \
            and not s.group_id and student_balance(db, s.id) >= 0:
        # "Chiqib ketgan" ham shu yerda arxivga o'tadi (2026-08-15)
        s.status = "archived"
        s.archive_when_paid = 0
        _sync_student_left_date(s)
        audit.log(db, user, entity="student", action="auto_archive",
                  entity_id=s.id, entity_label=s.full_name, field="status",
                  new_value="archived",
                  note="Qarz to'liq to'landi — avtomat arxivga o'tdi",
                  branch_id=s.branch_id)
        db.commit()

    # Telegram: ota-onaga chek — to'lov qabul qilindi (bog'langan bo'lsa)
    if payload.kind == "payment" and s.telegram_chat_id:
        try:
            bal = student_balance(db, s.id)
            notify.send(
                s.telegram_chat_id,
                f"✅ To'lov qabul qilindi\n{s.full_name}\n"
                f"Summa: {int(amount):,} so'm".replace(",", " ") +
                f"\nQoldiq balans: {int(bal):,} so'm".replace(",", " ") +
                f"\nQabul qildi: {user.full_name}")
        except Exception:
            pass

    # ---------------------------------------------------------------
    #  REFERAL (2026-08-28, Jahongir: "guruhga qo'yib to'lov qilgandan
    #  keyin 10% chegirma oladi"). Bu o'quvchi kimningdir havolasi
    #  orqali kelgan bo'lsa — o'sha odamning chegirmasi SHU YERDA,
    #  to'lov paytida hisoblanadi. Kechikkan hisob yo'q: bola to'lasa,
    #  do'sti chegirmani darrov ko'radi.
    #
    #  on_payment() HECH QACHON xato tashlamaydi: referal muammosi
    #  tufayli to'lov qabul qilish yiqilishi mumkin emas.
    # ---------------------------------------------------------------
    if payload.kind == "payment" and amount > 0:
        try:
            import referral as _ref
            res = _ref.on_payment(db, s)
            if res.get("ok") and res.get("friends"):
                ref = db.query(models.Student).get(res["referrer_id"])
                if ref is not None and ref.telegram_chat_id:
                    try:
                        notify.send(
                            ref.telegram_chat_id,
                            "🎉 Do'stingiz to'lov qildi!\n"
                            f"Sizda endi {res['percent']:.0f}% chegirma "
                            f"({res['friends']}-do'st).\n"
                            f"Summa: {int(res['amount']):,} so'm"
                            .replace(",", " ")
                            + f"\nQaysi oyga: {res['period']}")
                    except Exception:
                        pass
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    db.refresh(payment)
    return payment

@router.post("/api/students/{student_id}/activate")
def activate_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Sinovdagi (yoki muzlatilgan) o'quvchini FAOL qiladi.

    Guruhga qo'shilgan o'quvchi avtomat faol bo'lmaydi - avval sinov
    darsida turadi. Faollashtirish shu tugma orqali, ongli ravishda
    bo'ladi: shundan keyingina u hisob-kitobga to'liq kiradi."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
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

def fix_stale_group_links(db: Session) -> int:
    """KO'CHIRILGANDAN KEYIN ESKI GURUHDA QOLIB KETGANLARNI TUZATADI.

    2026-09-03, Jahongir: "bir o'quvchini boshqa guruhga o'tkizish
    qilsa eski guruhida qolyabdi ekan".

    Buzuq yozuvning ANIQ BELGISI: o'quvchining group_id si bor,
    lekin O'SHA guruh uchun faol bog'lanish YO'Q, ayni paytda
    BOSHQA guruhga faol bog'lanishi bor. Bu faqat eski (xato)
    ko'chirishdan keyin yuz beradi — chunki u paytda yangi guruh
    uchun bog'lanish umuman ochilmasdi.

    Haqiqiy ikki guruhli o'quvchida asosiy guruhning bog'lanishi
    HAR DOIM bo'ladi, shuning uchun ular bu shartga tushmaydi va
    ularga TEGILMAYDI.

    Yozuv o'chirilmaydi: eski bog'lanish active=0 bo'ladi, yangisi
    ochiladi. Tuzatilganlar sonini qaytaradi (idempotent)."""
    n = 0
    rows = (db.query(models.StudentGroupLink)
            .filter(models.StudentGroupLink.active == 1).all())
    by_student: dict = {}
    for l in rows:
        by_student.setdefault(l.student_id, []).append(l)
    for sid, links in by_student.items():
        s = db.query(models.Student).get(sid)
        if not s or not s.group_id:
            continue
        if any(l.group_id == s.group_id for l in links):
            continue          # asosiy guruh bog'langan — sog'lom
        # group_id boshqa guruhni ko'rsatyapti, bog'lanish esa eskisida
        for l in links:
            detach_group(db, s, l.group_id)
        link = attach_group(db, s, s.group_id)
        if link is not None:
            link.is_primary = 1

        n += 1
    if n:
        db.commit()
    return n


@router.post("/api/students/{student_id}/move-group")
def move_student_group(
    student_id: int,
    payload: schemas.StudentGroupMove,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Boshqa guruhga o'tkazadi. group_id bo'sh bo'lsa - guruhdan
    chiqaradi, lekin o'quvchi bazada qoladi (to'lov tarixi saqlanadi)."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    if payload.group_id is None:
        # Guruhdan chiqarish endi ALOHIDA endpoint orqali - sabab
        # majburiy va arxiv qoidalari ishlaydi.
        raise HTTPException(
            400, "Guruhdan chiqarish uchun sabab ko'rsatilishi shart — "
                 "'Guruhdan chiqarish' amalidan foydalaning")

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
    old_group = s.group
    s.group_id = g.id
    # Filial guruh bilan birga o'zgaradi - aks holda hisobotlar chalkashadi.
    if g.branch_id:
        s.branch_id = g.branch_id

    # ------------------------------------------------------------------
    # BOG'LANISH JADVALI (student_groups) — 2026-09-03 TUZATISH
    #
    # Jahongir: "bir o'quvchini boshqa guruhga o'tkizish qilsa eski
    # guruhida qolyabdi ekan".
    #
    # Sabab: bu yerda pastda `detach_group(db, s, g.id)` turardi —
    # ya'ni YANGI guruhning bog'lanishi yopilardi. ESKI guruhniki
    # esa faol qolib ketardi. Ro'yxatlar in_group() orqali ikkala
    # manbani ham o'qigani uchun o'quvchi ESKI guruhda ham,
    # yangisida ham ko'rinaverardi.
    #
    # Tartib o'quvchi kartasidagi to'g'ri yo'l bilan bir xil
    # (update_student): AVVAL yangisini qo'shamiz, KEYIN eskisini
    # yopamiz. Teskarisi qilinsa detach_group() ichidagi
    # sync_primary_group() group_id ni eski guruhga qaytarib
    # yuborishi mumkin.
    #
    # Yozuv O'CHIRILMAYDI — eski bog'lanish active=0 bo'lib,
    # chiqqan sanasi bilan tarixda qoladi.
    # ------------------------------------------------------------------
    link = attach_group(db, s, g.id, user)
    if old_group is not None and old_group.id != g.id:
        detach_group(db, s, old_group.id)
    # Ko'chirilgan guruh ASOSIY bo'lsin (ko'p guruhli o'quvchida ham)
    if link is not None:
        for other in (db.query(models.StudentGroupLink)
                      .filter(models.StudentGroupLink.student_id == s.id,
                              models.StudentGroupLink.group_id != g.id)
                      .all()):
            other.is_primary = 0
        link.is_primary = 1
    s.group_id = g.id
    db.commit()

    # MOLIYA: oy o'rtasida ko'chsa, shu oyning hisobi ikkiga bo'linib
    # qayta hisoblanadi (Jahongir, 2026-08-13: "narxi boshqa guruhga
    # o'tsa farqni qo'lda to'g'rilash kerak bo'lardi — shuni ham
    # avtomat qil").
    recharge = None
    try:
        recharge = _recharge_after_move(db, s, old_group, g, user=user)
        db.commit()
    except Exception:
        db.rollback()

    return {"ok": True, "group_id": g.id, "group": g.name,
            "recharge": recharge}

@router.get("/api/students/{student_id}/groups")
def student_groups(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """O'quvchining guruhlari (2026-08-17).

    Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi ...
    biz ham bazda 2ta gruppa qilishimiz kerak"."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    # O'Z-O'ZINI TUZATISH (2026-08-17). Bog'lanish jadvali kunlik
    # cron'da to'ldiriladi, lekin u ishlagunicha karta BO'SH
    # ko'rinardi — Jahongir: "munisaga kirsam ikkalasidam guruhsiz
    # bolib qolgan". Endi karta ochilganda yetishmayotgan bog'lanish
    # shu yerda yaratiladi: hech kim bo'sh karta ko'rmaydi.
    if s.group_id:
        try:
            have = (db.query(models.StudentGroupLink)
                    .filter(models.StudentGroupLink.student_id == s.id,
                            models.StudentGroupLink.group_id == s.group_id)
                    .first())
            if not have:
                attach_group(db, s, s.group_id, user,
                             joined=s.enrolled_date)
                db.commit()
        except Exception:
            db.rollback()
    rows = (db.query(models.StudentGroupLink, models.Group)
            .join(models.Group,
                  models.Group.id == models.StudentGroupLink.group_id)
            .filter(models.StudentGroupLink.student_id == s.id)
            .order_by(models.StudentGroupLink.active.desc(),
                      models.StudentGroupLink.is_primary.desc(),
                      models.StudentGroupLink.id).all())
    out = []
    for lk, g in rows:
        t = db.query(models.Teacher).get(g.teacher_id) if g.teacher_id else None
        room = db.query(models.Room).get(g.room_id) if g.room_id else None
        out.append({
            "id": lk.id, "group_id": g.id, "group": g.name,
            "subject": g.subject, "level": g.level,
            "teacher": t.full_name if t else None,
            "teacher_id": g.teacher_id,
            # LC UP dagidek to'liq karta uchun (2026-08-17)
            "lesson_days": g.lesson_days,
            "lesson_time": g.lesson_time,
            "room": (room.name if room else g.room),
            "monthly_fee": g.monthly_fee,
            "start_date": (g.start_date.isoformat()
                           if g.start_date else None),
            "lesson_price": lk.lesson_price or g.lesson_price,
            "is_primary": bool(lk.is_primary),
            "active": bool(lk.active),
            "joined_date": (lk.joined_date.isoformat()
                            if lk.joined_date else None),
            "left_date": (lk.left_date.isoformat()
                          if lk.left_date else None),
        })
    return {"rows": out,
            "active_count": sum(1 for r in out if r["active"]),
            "primary_group_id": s.group_id}


@router.post("/api/students/{student_id}/groups")
def student_add_group(
    student_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """O'quvchini YANA BIR guruhga qo'shish (2026-08-17).

    PUL MANTIG'IGA TEGILMAYDI — oylik hisob hozircha asosiy guruh
    bo'yicha chiqadi. Ikki fan uchun hisob va 10% chegirma keyingi
    bosqichda, Jahongir qoidani aytgach qo'shiladi."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    gid = (payload or {}).get("group_id")
    if not gid:
        raise HTTPException(400, "Guruhni tanlang")
    g = db.query(models.Group).get(int(gid))
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if s.branch_id and g.branch_id and s.branch_id != g.branch_id:
        raise HTTPException(
            400, "Guruh boshqa filialda — avval o'quvchining filialini "
                 "o'zgartiring.")
    exists = (db.query(models.StudentGroupLink)
              .filter(models.StudentGroupLink.student_id == s.id,
                      models.StudentGroupLink.group_id == g.id,
                      models.StudentGroupLink.active == 1).first())
    if exists:
        raise HTTPException(400, "O'quvchi bu guruhda allaqachon bor")
    attach_group(db, s, g.id, user, note=(payload or {}).get("note"))
    db.commit()
    audit.log(db, user, entity="student", action="update",
              entity_id=s.id, entity_label=s.full_name,
              field="Guruh qo'shildi", new_value=g.name,
              branch_id=s.branch_id, commit=True)
    return {"ok": True, "group": g.name,
            "active_count": len(student_group_ids(db, s.id))}


@router.delete("/api/students/{student_id}/groups/{group_id}")
def student_remove_group(
    student_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Bitta guruhdan chiqarish. Yozuv o'chirilmaydi — yopiladi.

    Oxirgi guruhdan chiqarish uchun eski "guruhdan chiqarish"
    tugmasi ishlatiladi (u hisobni ham to'g'rilaydi)."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if len(student_group_ids(db, s.id)) <= 1:
        raise HTTPException(
            400, "Bu oxirgi guruhi. Butunlay chiqarish uchun "
                 "\"Guruhdan chiqarish\" tugmasidan foydalaning — "
                 "u hisobni ham to'g'rilaydi.")
    g = db.query(models.Group).get(group_id)
    if not detach_group(db, s, group_id):
        raise HTTPException(404, "Bu guruhda emas")
    db.commit()
    audit.log(db, user, entity="student", action="update",
              entity_id=s.id, entity_label=s.full_name,
              field="Guruhdan olindi",
              old_value=g.name if g else str(group_id),
              branch_id=s.branch_id, commit=True)
    return {"ok": True,
            "active_count": len(student_group_ids(db, s.id))}


@router.post("/api/students/{student_id}/remove-from-group")
def remove_student_from_group(
    student_id: int,
    payload: schemas.RemoveFromGroupIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Guruhdan chiqarish — sabab MAJBURIY.

    2026-08-15, Jahongir: "guruhdan chiqqanda avtomat shu kungacha
    qatnashgan darslarini hisoblanib hisobi ham togrlanishi kerak, va
    guruhsiz bolishi kerak talab qarzi bolsa qarzdorlarda, qarzi yoq
    bolsa arxivga tushsin" + "birorta oquvchi guruhsiz lekin faol
    bola olmaydi".

    Tartib:
      1) SHU OYNING HISOBI QAYTA HISOBLANADI — chiqqan kungacha
         O'TILGAN darslar bo'yicha. Kelmagan darslar uchun pul
         qaytariladi (balans o'zi to'g'rilanadi).
      2) Guruhdan chiqariladi va holati "Chiqib ketgan" bo'ladi —
         FAOL bo'lib qolmaydi.
      3) Qarzi YO'Q  -> darhol arxivga tushadi;
         qarzi BOR   -> "Chiqib ketgan" bo'lib Qarzdorlar ro'yxatida
         qoladi, qarz to'liq to'langach AVTOMAT arxivga o'tadi.
    """
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.group_id:
        raise HTTPException(400, "O'quvchi hech qaysi guruhda emas")
    reason = (payload.reason or "").strip()
    if len(reason) < 3:
        raise HTTPException(400, "Chiqarish sababi majburiy — "
                                 "kamida bir necha so'z yozing")
    # KATEGORIYA MAJBURIY (2026-08-24, Jahongir: "ketish sababini
    # majburiy qil"). Sababsiz ketish — analitikada "noma'lum"
    # bo'lib qoladi va nima tuzatish kerakligi ko'rinmaydi.
    code = (payload.reason_code or "").strip()
    if code not in roles.LEAVE_REASON_LABELS:
        raise HTTPException(
            400, "Ketish sababini ro'yxatdan tanlang — statistika "
                 "shu asosda yig'iladi (narx, ustoz, vaqt, natija...)")

    # QAYSI KUNGACHA (2026-08-20, Jahongir: "guruhdan talabani
    # chiqarishda, sana tanlaydigan bo'lsin va masalan tanlangan
    # sanagacha hisoblanib hisobi o'zgarsin va guruhdan chiqarilsin").
    # Ilgari doim "bugun" olinardi — administrator kechikib kiritsa
    # o'quvchidan ortiqcha pul yechilib qolardi.
    on = payload.on_date or roles.local_today()
    _today = roles.local_today()
    if on > _today:
        raise HTTPException(400, "Kelajakdagi sanani tanlab bo'lmaydi")
    if s.enrolled_date and on < s.enrolled_date:
        raise HTTPException(
            400, f"Sana qo'shilgan kunidan oldin bo'lishi mumkin emas "
                 f"({s.enrolled_date.isoformat()})")

    group = s.group
    old_group = group.name if group else None
    # 1) Hisobni TANLANGAN kungacha o'tilgan darslar bo'yicha to'g'rilash
    recalc = None
    try:
        recalc = _recharge_on_leave(db, s, group, on=on, user=user)
        if recalc:
            db.flush()
    except Exception:
        recalc = None

    bal = student_balance(db, s.id)
    # Ketish sababi — analitika uchun (bir o'quvchiga bitta yozuv)
    if not db.query(models.LeaveReason).filter(
            models.LeaveReason.student_id == s.id).first():
        db.add(models.LeaveReason(
            student_id=s.id, reason=code, note=reason,
            group_id=s.group_id,
            teacher_id=(group.teacher_id if group else None),
            left_date=on, created_by=user.full_name))
    s.group_id = None

    if bal < 0:
        # Qarzdor: arxivga EMAS — "chiqib ketgan" bo'lib qoladi va
        # Qarzdorlar ro'yxatida ko'rinaveradi. Faol emas.
        s.status = roles.STUDENT_LEFT
        s.archive_when_paid = 1
        debt = int(-bal)
        note = (f"Sabab: {reason} · Qarzi bor "
                f"({debt:,} so'm) — to'langach avtomat arxivga o'tadi"
                .replace(",", " "))
        archived = False
    else:
        s.status = "archived"
        s.archive_when_paid = 0
        # Ketgan sana — TANLANGAN kun (hisobotlar shu kun bo'yicha
        # chiqadi, 2026-08-20).
        s.left_date = on
        archived = True
        note = f"Sabab: {reason} · Arxivga o'tkazildi"
    note += f" · Chiqarilgan sana: {on.isoformat()}"
    if recalc:
        note += (f" · Hisob to'g'rilandi: {recalc['lessons']} dars, "
                 f"{int(recalc['returned']):,} so'm qaytarildi"
                 .replace(",", " "))

    audit.log(db, user, entity="student", action="group_remove",
              entity_id=s.id, entity_label=s.full_name, field="group",
              old_value=old_group, new_value=None, note=note,
              branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "archived": archived,
            "status": s.status,
            "on_date": on.isoformat(),
            "recalc": recalc,
            "debt": int(-bal) if bal < 0 else 0}


@router.get("/api/students/{student_id}/leave-preview")
def leave_preview(
    student_id: int,
    on_date: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Guruhdan chiqarishdan OLDIN: tanlangan sanagacha nechta dars
    hisoblanadi va balans qanday bo'ladi (2026-08-20).

    Hech narsa o'zgartirmaydi — administrator raqamni ko'rib turib
    tugmani bosadi, keyin "nega bunday summa" degan savol chiqmaydi.
    """
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    g = s.group
    try:
        on = (date.fromisoformat(on_date) if on_date
              else roles.local_today())
    except ValueError:
        raise HTTPException(400, "Sana formati noto'g'ri")

    current = student_balance(db, s.id)
    if g is None:
        return {"lessons": 0, "current": current, "target": current,
                "returned": 0, "changed": False,
                "hint": "O'quvchi guruhda emas"}

    start, _end = billing.month_bounds(on.year, on.month)
    frm = start
    if s.enrolled_date and s.enrolled_date > start:
        frm = s.enrolled_date
    held = (db.query(models.Lesson)
            .filter(models.Lesson.group_id == g.id,
                    models.Lesson.held == 1,
                    models.Lesson.date >= frm,
                    models.Lesson.date <= on).count())
    cap = int(getattr(g, "standard_lessons_per_month", None) or 12)
    n = min(held, cap)
    try:
        disc = float(_student_discount_percent(db, s) or 0)
    except Exception:
        disc = 0.0
    unit = billing.student_lesson_price(s, g) * (100.0 - disc) / 100.0
    target_charge = roles.money(n * unit)

    period = f"{on.year:04d}-{on.month:02d}"
    row = (db.query(models.Payment)
           .filter(models.Payment.student_id == s.id,
                   models.Payment.kind == "charge",
                   models.Payment.period == period)
           .order_by(models.Payment.id.desc()).first())
    was = abs(float(row.amount or 0)) if row is not None else 0.0
    returned = round(was - target_charge) if row is not None else 0
    return {
        "lessons": n,
        "price": round(unit),
        "discount": disc,
        "was": round(was),
        "charge": round(target_charge),
        "returned": returned,
        "current": round(current),
        "target": round(current + returned),
        "changed": bool(row is not None and abs(returned) >= 1),
        "hint": (f"{on.isoformat()} kunigacha {n} ta dars o'tilgan"
                 if row is not None else
                 "Bu oy uchun hisob chiqarilmagan — balans o'zgarmaydi"),
    }

@router.post("/api/students/{student_id}/restore")
def restore_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Arxivdagi o'quvchini qayta tiklaydi — o'quvchilar qaytib kelishi
    mumkin. Holati FAOL bo'ladi, guruh esa bo'sh qoladi: keyin qo'lda
    kerakli guruhga qo'shiladi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if s.status not in ("archived", roles.STUDENT_LEFT):
        raise HTTPException(400, "Bu o'quvchi arxivda emas")
    s.status = "active"
    s.archive_when_paid = 0
    _sync_student_left_date(s)
    audit.log(db, user, entity="student", action="restore", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value="archived", new_value="active",
              note="Arxivdan qayta tiklandi", branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "status": s.status}

@router.get("/api/students/{student_id}/talks")
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

@router.post("/api/students/{student_id}/talks")
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

@router.get("/api/students/{student_id}/certificates")
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

@router.post("/api/students/{student_id}/certificates")
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

_STATUS_EVENT = {
    "frozen": ("freeze", "O'qish muzlatildi"),
    "archived": ("leave", "O'qishdan chiqdi"),
    "active": ("return", "Qayta tiklandi"),
    "trial": ("trial", "Sinov darsiga o'tdi"),
}

@router.get("/api/students/{student_id}/history")
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
        _detail = f"{l.old_value or '—'} → {l.new_value or '—'}"
        # Chiqarish sababi tarixda ko'rinadi — ustozlar o'quvchi nega
        # ketganini shu yerdan biladi.
        if l.note:
            _detail += f" · {l.note}"
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": "group",
            "title": "Guruhdan chiqarildi" if l.action == "group_remove"
                     else "Guruh almashtirildi",
            "detail": _detail,
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

    # --- Platformadagi BOSHQA BARCHA amallar (audit) ---
    # Yuqorida maxsus ko'rinishda chiqarilganlari takrorlanmaydi.
    handled = {"group_move", "group_remove"}
    ACTION_UZ = {
        "create": "Yaratildi", "update": "Tahrirlandi",
        "freeze": "Muzlatildi", "auto_freeze": "Avtomuzlatildi",
        "activate": "Faollashtirildi", "to_trial": "Sinovga qaytarildi",
        "to_lead": "Lidga qaytarildi", "archive": "Arxivlandi",
        "delete": "O'chirildi",
        "group_remove": "Guruhdan chiqarildi",
        "group_move": "Guruh almashtirildi",
        "auto_archive": "Qarz to'landi — avtomat arxivlandi",
        "restore": "Arxivdan qayta tiklandi",
    }
    for l in logs:
        if l.action in handled:
            continue
        if l.field == "status" or l.action == "activate":
            pass  # holat o'zgarishlari ham ko'rinsin
        detail = ""
        if l.old_value or l.new_value:
            detail = f"{l.old_value or '—'} → {l.new_value or '—'}"
        if l.note:
            detail = (detail + " · " if detail else "") + l.note
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": "audit",
            "title": ACTION_UZ.get(l.action, l.action)
                     + (f" ({l.field})" if l.field else ""),
            "detail": detail or None,
            "by": l.user_name,
        })
    # To'lov amallari ham shu bolaga tegishli bo'lsa — tarixga
    pay_ids = [pid for (pid,) in db.query(models.Payment.id).filter(
        models.Payment.student_id == student_id).all()]
    if pay_ids:
        for l in (db.query(models.AuditLog)
                  .filter(models.AuditLog.entity == "payment",
                          models.AuditLog.entity_id.in_(pay_ids))
                  .order_by(models.AuditLog.created_at).all()):
            timeline.append({
                "date": l.created_at.isoformat() if l.created_at else None,
                "kind": "payment",
                "title": f"To'lov amali: {l.action}",
                "detail": (l.new_value or "") + (
                    f" · {l.note}" if l.note else "") or None,
                "by": l.user_name,
            })
    timeline.sort(key=lambda e: e["date"] or "", reverse=True)

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

@router.get("/api/students/{student_id}/discounts")
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
    # 2026-08-12, Jahongir: "10% chegirma berganimdan keyin jami
    # chegirmada 0% turibdi". Sabab: chegirmaning boshlanish sanasi
    # KELAJAKDA edi (01.09) - ya'ni bugun hali amal qilmaydi. Raqam
    # to'g'ri edi, lekin ekranda buning izohi yo'q edi. Endi
    # "keyinroq boshlanadi" alohida ko'rsatiladi.
    fee = s.group.monthly_fee if s.group else 0.0
    upcoming = 0.0
    upcoming_from = None
    today = date.today()
    for d in rows:
        if d.status != "active" or not d.start_date or d.start_date <= today:
            continue
        if d.end_date and d.end_date < today:
            continue
        if d.kind == "family":
            continue
        if d.percent:
            upcoming += d.percent
        elif d.amount and fee:
            upcoming += d.amount / fee * 100
        if upcoming_from is None or d.start_date < upcoming_from:
            upcoming_from = d.start_date
    return {
        "rows": [_discount_out(db, d) for d in rows],
        "family_percent": fam,
        "total_percent": _student_discount_percent(db, s),
        "upcoming_percent": round(upcoming, 2),
        "upcoming_from": upcoming_from.isoformat() if upcoming_from else None,
        "max_percent": roles.MAX_TOTAL_DISCOUNT_PERCENT,
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "types": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.DISCOUNT_TYPES
                  if k not in roles.AUTO_DISCOUNT_TYPES],
    }

@router.get("/api/students/{student_id}/pricing")
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
    # ESKI NARX HIMOYASI (2026-08-15): o'quvchida qulflangan narx
    # bo'lsa oylik shundan hisoblanadi, guruh narxidan emas.
    locked = getattr(s, "locked_lesson_price", None)
    if locked and s.group:
        base = round(float(locked)
                     * (s.group.standard_lessons_per_month or 12))
    fam = _family_discount_percent(db, s)

    # Shartnomadagi shaxsiy chegirma (agar bo'lsa)
    contract = (db.query(models.Contract)
                .filter(models.Contract.student_id == student_id,
                        models.Contract.status == "active")
                .order_by(models.Contract.date.desc()).first())
    personal = contract.discount_percent if contract else 0.0
    if contract and contract.monthly_fee:
        base = contract.monthly_fee

    # Tasdiqlangan va BUGUN amalda bo'lgan chegirmalar (referral, grant,
    # individual...). Ilgari bu blok faqat shartnomadagi foizni
    # ko'rsatardi - o'quvchiga 10% chegirma berilsa ham "To'lanadigan"
    # o'zgarmasdi (Jahongir, 2026-08-12).
    granted = 0.0
    for d in db.query(models.Discount).filter(
            models.Discount.student_id == student_id,
            models.Discount.status == "active").all():
        if d.kind == "family" or not _discount_alive(d):
            continue
        if d.percent:
            granted += d.percent
        elif d.amount and base:
            granted += d.amount / base * 100
    granted = round(granted, 2)

    siblings = []
    if s.parent_id:
        siblings = [{"id": x.id, "full_name": x.full_name, "status": x.status}
                    for x in db.query(models.Student).filter(
                        models.Student.parent_id == s.parent_id,
                        models.Student.id != s.id).all()]

    total_pct = min(100.0, fam + personal + granted)
    return {
        "base_fee": base,
        "family_discount": fam,
        "family_min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "personal_discount": personal,
        "granted_discount": granted,
        "total_discount": total_pct,
        "final_fee": round(base * (100 - total_pct) / 100, 2),
        "parent_id": s.parent_id,
        # Eski narx himoyasi (2026-08-15)
        "locked_lesson_price": locked,
        "locked_price_note": getattr(s, "locked_price_note", None),
        "locked_price_at": (s.locked_price_at.isoformat()
                            if getattr(s, "locked_price_at", None)
                            else None),
        "current_lesson_price": (s.group.lesson_price if s.group else None),
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

@router.get("/api/family-search")
def family_search(
    q: str,
    other_branch: int = 0,
    exclude: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    """Oila a'zosini qidirish — kerak bo'lsa BOSHQA FILIALLARDAN ham.

    2026-08-14, Jahongir: "boshqa filialda oila azosi oqishiyam mumkin
    ... 'boshqa filialda' degan ptichka qo'yadigan joy chiqsa, agar
    bossa boshqa filial o'quvchilari orasidan chiqadi, bosmasa o'zini
    filialidan qidiradi".

    Javobda faqat ism, guruh va filial bo'ladi — pul ma'lumoti yo'q,
    shuning uchun boshqa filialni ko'rish maxfiylikni buzmaydi.
    """
    q = (q or "").strip()
    if len(q) < 3:
        return []
    like = f"%{q}%"
    query = db.query(models.Student).filter(
        models.Student.full_name.ilike(like))
    if other_branch:
        # Boshqa filiallar: o'z filiali CHIQARIB tashlanadi, qolgan
        # hammasi ko'rinadi (oila boshqa filialda o'qiyotgan bo'lsa).
        mine = _user_branch_ids(db, user)
        if exclude:
            me = db.query(models.Student).get(exclude)
            if me and me.branch_id:
                mine = [me.branch_id]
        if mine:
            query = query.filter(
                or_(models.Student.branch_id.is_(None),
                    models.Student.branch_id.notin_(mine)))
    else:
        query = scope_to_branch(query, models.Student, user)
    rows = query.order_by(models.Student.full_name).limit(15).all()
    out = []
    for x in rows:
        if exclude and x.id == exclude:
            continue
        out.append({
            "id": x.id,
            "full_name": x.full_name,
            "group": x.group.name if x.group else None,
            "branch": x.branch.name if x.branch else None,
            "status": x.status,
        })
    return out


@router.post("/api/students/{student_id}/family-link")
def student_family_link(
    student_id: int,
    payload: schemas.FamilyLinkIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    """Ikki o'quvchini BIR OILA deb bog'lash.

    2026-08-12, Jahongir: "agar bir xil familya bo'lsa, qiz bolada
    oxir fozilova o'gil bolada fozilov bo'lsa ham avtomat tizim
    tasdiqlayversin, lekin agar boshqa familya bolsa sorov bolib
    vazifa bolib tushsin".

    Ya'ni: familiya bir xil bo'lsa (yoki so'ragan odamning o'zi
    tasdiqlash huquqiga ega bo'lsa) - darrov bog'lanadi. Familiya
    boshqa bo'lsa - "tasdiq kutmoqda" holatidagi so'rov yoziladi va
    filial rahbari, moliyachi hamda asoschiga vazifa tushadi.
    """
    a = db.query(models.Student).get(student_id)
    b = db.query(models.Student).get(payload.sibling_id)
    if not a or not b:
        raise HTTPException(404, "O'quvchi topilmadi")
    if a.id == b.id:
        raise HTTPException(400, "O'quvchini o'ziga bog'lab bo'lmaydi")
    if a.parent_id and a.parent_id == b.parent_id:
        raise HTTPException(400, "Bular allaqachon bir oila")

    same = _same_surname(a.full_name, b.full_name)
    can_approve = user.role in tuple(roles.DISCOUNT_APPROVE)

    if same or can_approve:
        out = _do_family_link(db, a, b, user.username)
        audit.log(db, user, entity="student", action="family_link",
                  entity_id=a.id, entity_label=a.full_name,
                  branch_id=a.branch_id,
                  new_value=f"{a.full_name} + {b.full_name} = bir oila"
                            + (" (familiya bir xil - avtomat)" if same
                               else " (rahbar bog'ladi)"),
                  commit=True)
        out["status"] = "linked"
        if same and not can_approve:
            out["message"] += " Familiya bir xil bo'lgani uchun tasdiq " \
                              "so'ralmadi."
        return out

    # Familiya boshqa - tasdiqqa yuboriladi. So'rov CHEGIRMA yozuvi
    # sifatida saqlanadi: tasdiqlash/rad etish tugmalari allaqachon
    # o'sha yerda va tarix ham bir joyda qoladi.
    dup = (db.query(models.Discount)
           .filter(models.Discount.student_id == a.id,
                   models.Discount.kind == "family",
                   models.Discount.referrer_student_id == b.id,
                   models.Discount.status == "pending").first())
    if dup:
        raise HTTPException(400, "Bu so'rov allaqachon yuborilgan")
    d = models.Discount(
        student_id=a.id, kind="family",
        percent=roles.FAMILY_DISCOUNT_PERCENT,
        reason=f"Oila: {b.full_name} bilan bog'lash so'rovi "
               f"(familiyalar har xil)",
        start_date=date.today(),
        referrer_student_id=b.id,
        requested_by=user.full_name,
        status="pending")
    db.add(d); db.commit(); db.refresh(d)
    _notify_discount_approvers(db, d, a, extra=(
        f"Familiyalar har xil ({a.full_name} / {b.full_name}) — "
        f"shuning uchun tasdiq so'ralmoqda."))
    audit.log(db, user, entity="discount", action="create", entity_id=d.id,
              entity_label=a.full_name, branch_id=a.branch_id,
              new_value=f"Oila so'rovi: {b.full_name}", commit=True)
    return {
        "status": "pending",
        "discount_id": d.id,
        "family_percent": 0.0,
        "active_children": 0,
        "children": [],
        "message": ("Familiyalar har xil — so'rov filial rahbari, "
                    "moliyachi va asoschiga vazifa bo'lib yuborildi. "
                    "Tasdiqlangach ikkalasiga 10% avtomat hisoblanadi."),
    }

@router.get("/api/students/{student_id}/trial")
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

@router.get("/api/archive/students")
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

@router.get("/api/archive/staff")
def archive_staff(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    """Ishdan bo'shagan xodimlar - qanday ajrashilgani bo'yicha.
    Qayta ishga olish masalasida shu ro'yxat hal qiluvchi."""
    q = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 0)
    rows = [{
        "id": u.id, "kind": "user",
        "public_id": u.public_id, "full_name": u.full_name,
        "username": u.username, "role": u.role,
        "role_label": roles.UZ_LABELS.get(u.role, u.role),
        "branch": u.branch.name if u.branch else None,
        "exit_type": u.exit_type or "neutral",
        "exit_label": roles.EXIT_TYPE_LABELS.get(u.exit_type or "neutral",
                                                 "Neytral"),
        "exit_reason": u.exit_reason,
        "exit_date": u.exit_date.isoformat() if u.exit_date else None,
    } for u in q.all()]
    # Hisob ochilmagan, ishdan ketgan USTOZ KARTALARI ham arxivda
    # ko'rinadi — O'qituvchilar bo'limida "ketgan" bo'lib yotmaydi.
    tq = scope_to_branch(db.query(models.Teacher), models.Teacher,
                         user).filter(models.Teacher.is_active == 0,
                                      models.Teacher.user_id.is_(None))
    for t in tq.all():
        rows.append({
            "id": -t.id, "kind": "teacher", "teacher_id": t.id,
            "public_id": None, "full_name": t.full_name,
            "username": "ustoz kartasi", "role": "teacher",
            "role_label": "O'qituvchi",
            "branch": t.branch.name if t.branch else None,
            "exit_type": "neutral",
            "exit_label": roles.EXIT_TYPE_LABELS.get("neutral", "Neytral"),
            "exit_reason": None,
            "exit_date": t.left_date.isoformat() if t.left_date else None,
        })
    rows.sort(key=lambda r: (r["exit_date"] or "", r["full_name"]), reverse=True)

    groups = []
    for key, label, hint in roles.EXIT_TYPES:
        groups.append({
            "key": key, "label": label, "hint": hint,
            "count": sum(1 for r in rows if r["exit_type"] == key),
        })
    return {"groups": groups, "rows": rows, "total": len(rows)}

@router.put("/api/archive/staff/{user_id}")
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

@router.get("/api/students/{student_id}/debt-contacts")
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

@router.post("/api/students/{student_id}/leave-reason")
def set_leave_reason(
    student_id: int,
    payload: schemas.LeaveReasonCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
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

@router.post("/api/students/{student_id}/link-account")
def link_student_account(
    student_id: int,
    payload: schemas.LinkAccount,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.USER_ADMIN)),
):
    """O'quvchiga kirish hisobi ochish. Shundan keyin u kirib coin
    balansini ko'radi va sovg'a so'ray oladi."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if db.query(models.User).filter(
            models.User.username == payload.username).first():
        raise HTTPException(400, "Bu login band")
    if not roles.password_ok(payload.password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)

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

@router.get("/api/students/{student_id}/gamification")
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

@router.post("/api/students/{student_id}/freeze")
def freeze_student(student_id: int, payload: schemas.FreezeIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FREEZE_ROLES))):
    """O'quvchini muzlatish. Qaytish sanasi MAJBURIY — shu sanada
    adminlarga 'aloqaga chiqing' vazifasi tushadi."""
    st = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.until <= roles.local_today():
        raise HTTPException(400, "Qaytish sanasi kelajakda bo'lishi kerak")
    st.status = "frozen"
    st.frozen_until = payload.until
    st.frozen_note = payload.note
    _freeze_task(db, st, payload.until, payload.note)
    db.commit()
    audit.log(db, user, entity="student", action="freeze",
              entity_id=st.id, entity_label=st.full_name,
              new_value=f"qaytishi: {payload.until.isoformat()}",
              note=payload.note, commit=True)
    return {"ok": True}

@router.post("/api/students/{student_id}/to-trial")
def student_to_trial(student_id: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faol o'quvchini sinov darsiga qaytarish."""
    st = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if st.status != "active":
        raise HTTPException(400, "Faqat faol o'quvchi sinovga qaytariladi")
    st.status = "trial"
    db.commit()
    audit.log(db, user, entity="student", action="to_trial",
              entity_id=st.id, entity_label=st.full_name, commit=True)
    return {"ok": True}

@router.post("/api/students/{student_id}/to-lead")
def student_to_lead(student_id: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faollashtirilmagan (sinovdagi) talabani lidlar doskasiga
    qaytarish."""
    st = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if st.status != "trial":
        raise HTTPException(
            400, "Faqat faollashtirilmagan (sinovdagi) talaba lidga "
                 "qaytariladi")
    lead = db.query(models.Lead).filter(
        models.Lead.converted_student_id == st.id).first()
    if lead:
        lead.stage = "trial_scheduled"
        lead.converted_student_id = None
    else:
        db.add(models.Lead(full_name=st.full_name, phone=st.phone,
                           source="other", stage="trial_scheduled",
                           branch_id=st.branch_id,
                           note="O'quvchilar ro'yxatidan qaytarildi",
                           created_by=user.full_name))
    st.status = "archived"
    st.note = ((st.note + " · ") if st.note else "") + "Lidga qaytarildi"
    db.commit()
    audit.log(db, user, entity="student", action="to_lead",
              entity_id=st.id, entity_label=st.full_name, commit=True)
    return {"ok": True}

@router.get("/api/students/{student_id}/purchases")
def student_purchases(student_id: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF))):
    """Coin do'konidan qilingan xaridlar ro'yxati."""
    if not db.query(models.Student).get(student_id):
        raise HTTPException(404, "O'quvchi topilmadi")
    rewards = {r.id: r for r in db.query(models.Reward).all()}
    rows = (db.query(models.RewardRedemption)
            .filter(models.RewardRedemption.student_id == student_id)
            .order_by(models.RewardRedemption.id.desc()).all())
    ST = {"given": "berildi", "pending": "kutilmoqda",
          "approved": "tasdiqlandi", "rejected": "rad etildi",
          "cancelled": "bekor"}
    return {"purchases": [{
        "id": r.id,
        "reward": rewards[r.reward_id].name
        if r.reward_id in rewards else "—",
        "coins": r.coins,
        "value_som": rewards[r.reward_id].value_som
        if r.reward_id in rewards else None,
        "status": ST.get(r.status, r.status),
        "by_student": bool(r.requested_by_student),
        "date": r.given_at.date().isoformat() if r.given_at else None,
    } for r in rows],
        "total_coins": sum(r.coins or 0 for r in rows
                           if r.status != "rejected")}

@router.get("/api/students/{student_id}/reminders")
def student_reminders(student_id: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF))):
    rows = (db.query(models.StudentReminder)
            .filter(models.StudentReminder.student_id == student_id)
            .order_by(models.StudentReminder.done,
                      models.StudentReminder.remind_on.is_(None),
                      models.StudentReminder.remind_on,
                      models.StudentReminder.id.desc()).all())
    return {"reminders": [{
        "id": r.id, "text": r.text,
        "remind_on": r.remind_on.isoformat() if r.remind_on else None,
        "done": bool(r.done), "created_by": r.created_by,
        "date": r.created_at.date().isoformat() if r.created_at else None,
        "overdue": bool(r.remind_on and not r.done
                        and r.remind_on <= roles.local_today()),
    } for r in rows]}

@router.post("/api/students/{student_id}/reminders")
def add_student_reminder(student_id: int, payload: schemas.ReminderIn,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.TEACHING_STAFF))):
    """Eslatma qo'shish. Sana ko'rsatilsa — o'sha kuni admin va sotuv
    menejeriga vazifa tushadi."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not (payload.text or "").strip():
        raise HTTPException(400, "Eslatma matnini yozing")
    r = models.StudentReminder(
        student_id=student_id, text=payload.text.strip(),
        remind_on=payload.remind_on, created_by=user.full_name)
    db.add(r)
    if payload.remind_on:
        days = max((payload.remind_on - roles.local_today()).days, 1)
        _hr_task(db, title=f"Eslatma: {st.full_name}",
                 body=f"{payload.text.strip()} — {user.full_name} "
                      f"qoldirgan eslatma.",
                 to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER],
                 branch_id=st.branch_id, days=days, priority="normal")
    db.commit()
    audit.log(db, user, entity="student", action="reminder",
              entity_id=st.id, entity_label=st.full_name,
              new_value=payload.text.strip()[:80],
              note=payload.remind_on.isoformat()
              if payload.remind_on else None, commit=True)
    return {"ok": True, "id": r.id}

@router.post("/api/students/{student_id}/reminders/{rid}/toggle")
def toggle_student_reminder(student_id: int, rid: int,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.TEACHING_STAFF))):
    r = db.query(models.StudentReminder).get(rid)
    if not r or r.student_id != student_id:
        raise HTTPException(404, "Eslatma topilmadi")
    r.done = 0 if r.done else 1
    db.commit()
    return {"ok": True, "done": bool(r.done)}

def _tg_gen_code(db: Session, s: models.Student) -> str:
    if not s.tg_code:
        import secrets as _sec
        s.tg_code = f"S{s.id}{_sec.token_hex(2).upper()}"
        db.commit()
    return s.tg_code

@router.get("/api/students/{student_id}/telegram")
def student_telegram(student_id: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.CASH_ACCESS))):
    """O'quvchi kartasidagi Telegram bo'lagi: ulanganmi, kod qanday."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not notify.enabled():
        return {"enabled": False}
    return {
        "enabled": True,
        "linked": bool(s.telegram_chat_id),
        "code": _tg_gen_code(db, s),
        "bot": notify.bot_info(),
    }

@router.post("/api/students/{student_id}/notify-debt")
def notify_debt(student_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.CASH_ACCESS))):
    """Qarzdorlik eslatmasi — admin tugma bosganda ota-onaga boradi."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.telegram_chat_id:
        return {"sent": False, "reason": "Telegram ulanmagan"}
    bal = student_balance(db, s.id)
    if bal >= 0:
        return {"sent": False, "reason": "Qarzdorlik yo'q"}
    sent = notify.send(
        s.telegram_chat_id,
        f"💰 Eslatma: {s.full_name} bo'yicha "
        f"{int(-bal):,} so'm to'lov qoldi.".replace(",", " ") +
        "\nMarkazga to'lab ketishingizni so'raymiz. Rahmat!")
    if sent:
        audit.log(db, user, entity="student", action="notify_debt",
                  entity_id=s.id, entity_label=s.full_name,
                  branch_id=s.branch_id, commit=True)
    return {"sent": sent}

def _new_parent_token(s: models.Student) -> None:
    """Yangi (yoki birinchi) ota-ona tokeni + muddatini o'rnatadi.
    Chaqiruvchi commit qiladi."""
    import secrets as _sec
    s.parent_token = _sec.token_urlsafe(16)
    s.parent_token_expires_at = (
        datetime.utcnow()
        + timedelta(days=roles.PARENT_TOKEN_VALIDITY_DAYS))


@router.get("/api/students/{student_id}/parent-link")
def parent_link(student_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.CASH_ACCESS))):
    """Ota-onaga beriladigan havola. Token taxmin qilib bo'lmaydigan
    tasodifiy satr, roles.PARENT_TOKEN_VALIDITY_DAYS kundan keyin
    muddati tugaydi - kerak bo'lsa /regenerate bilan almashtiriladi.

    Bu endpoint MAVJUD havolani hech qachon bekor qilmaydi (shunchaki
    ko'rish/nusxalash uchun ochilganda ham tasodifan almashtirib
    qo'ymaslik uchun) - faqat token umuman yo'q bo'lsa yaratadi, yoki
    muddat tizimidan OLDINGI eski tokenga (parent_token_expires_at
    NULL) endi ham amal qiladigan muddat belgilaydi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.parent_token:
        _new_parent_token(s)
        db.commit()
    elif not s.parent_token_expires_at:
        s.parent_token_expires_at = (
            datetime.utcnow()
            + timedelta(days=roles.PARENT_TOKEN_VALIDITY_DAYS))
        db.commit()
    base = os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app")
    return {"url": f"{base}/parent/{s.parent_token}",
            "expires_at": s.parent_token_expires_at.isoformat()}


@router.post("/api/students/{student_id}/parent-link/regenerate")
def parent_link_regenerate(student_id: int, db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.CASH_ACCESS))):
    """Eski havolani DARHOL bekor qiladi (endi ishlamaydi) va yangisini
    yaratadi. Token noto'g'ri odamga ketgan yoki muddati tugagan
    bo'lsa ishlatiladi."""
    s = _get_student_in_scope(db, student_id, user)  # filial chegarasi (2026-09-06)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    had_old = bool(s.parent_token)
    _new_parent_token(s)
    db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, field="Ota-ona havolasi",
              old_value="eski havola bekor qilindi" if had_old else "yo'q edi",
              new_value="yangi havola yaratildi", commit=True)
    base = os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app")
    return {"url": f"{base}/parent/{s.parent_token}",
            "expires_at": s.parent_token_expires_at.isoformat()}

@router.get("/api/students/{student_id}/pay-link")
def pay_link(student_id: int, amount: float = 0,
             db: Session = Depends(get_db),
             user=Depends(require_role(*roles.CASH_ACCESS))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    payme_id = os.environ.get("PAYME_MERCHANT_ID", "").strip()
    click_m = os.environ.get("CLICK_MERCHANT_ID", "").strip()
    click_s = os.environ.get("CLICK_SERVICE_ID", "").strip()
    if not payme_id and not (click_m and click_s):
        return {"enabled": False}
    amt = roles.money(amount) if amount and amount > 0 \
        else roles.money(-student_balance(db, s.id)
                         if student_balance(db, s.id) < 0 else 0)
    links = {}
    if payme_id and amt > 0:
        import base64 as _b64
        raw = f"m={payme_id};ac.student={s.public_id or s.id};a={int(amt * 100)}"
        links["payme"] = ("https://checkout.paycom.uz/"
                          + _b64.b64encode(raw.encode()).decode())
    if click_m and click_s and amt > 0:
        links["click"] = (
            "https://my.click.uz/services/pay"
            f"?service_id={click_s}&merchant_id={click_m}"
            f"&amount={int(amt)}&transaction_param={s.public_id or s.id}")
    return {"enabled": True, "amount": amt, "links": links}

# =====================================================================
#  IMPORTNI BEKOR QILISH  (2026-08-28)
# =====================================================================
#
#  Jahongir: "hozir Elena rus tili ... filialdagi guruhga o'quvchi
#  import qilib 167 ta o'quvchini kirgizvoribman ADASHIB, nima
#  qilsam bo'ladi"
#
#  Import 167 ta qator yaratdi. Ularni birma-bir o'chirish — bir
#  necha soatlik ish va yo'lda haqiqiy o'quvchini ham o'chirib
#  yuborish xavfi bor. Shuning uchun BATAFSIL, ORQAGA QAYTARIB
#  BO'LADIGAN yo'l:
#
#   1) OLDIN KO'RSATADI. Hech narsaga tegmasdan ro'yxat chiqadi:
#      kim, qachon kiritilgan, tarixi bormi.
#   2) TARIXI BORINI TEGMAYDI. To'lovi, yo'qlamasi, coini, imtihoni
#      yoki ilova faolligi bo'lgan o'quvchi HIMOYALANGAN — u
#      haqiqiy odam bo'lishi mumkin. U alohida ro'yxatda chiqadi
#      va qo'lda hal qilinadi.
#   3) FAQAT TASDIQLANGANINI QAYTARADI. Haqiqiy bajarishda server
#      o'zi tanlamaydi: brauzer aynan qaysi ID larni tasdiqlagan
#      bo'lsa, o'shalarni oladi.
#   4) IKKI BOSQICH. Standart — ARXIVGA (qaytarib bo'ladi). Butunlay
#      o'chirish faqat asoschida va faqat tarixsizlar uchun.
#
# ODAM QILGAN ish bo'lgan jadvallar. Bittasi ham bo'lsa —
# o'quvchi HIMOYALANADI, bekor qilinmaydi.
_ACTIVITY_TABLES = [
    ("attendances", "yo'qlama"),
    ("coin_entries", "coin"),
    ("exam_results", "imtihon"),
    ("vocab_attempts", "ilovada mashq"),
    ("discounts", "chegirma"),
]


def _student_activity(db: Session, ids: list) -> tuple:
    """Qaysi o'quvchida qanday iz bor.

    ENG NOZIK JOY — HISOB (charge) IZ EMAS.

    Xato import qilinganda tizim har bir yangi o'quvchiga o'zi oylik
    HISOB yozadi (kind="charge", ya'ni qarz). Agar shuni ham "tarixi
    bor" deb hisoblasak, 167 tasining HAMMASI himoyalanib qolardi va
    bekor qilish umuman ishlamasdi — aynan shu holat test paytida
    chiqdi.

    Shuning uchun to'lov jadvali TURI bo'yicha ajratiladi:
      · charge  — tizim o'zi yozgan hisob, ODAM QILGAN ish emas ->
                  iz emas, o'quvchi bilan birga tozalanadi;
      · payment/discount/refund — HAQIQIY pul harakati -> iz,
                  o'quvchi himoyalanadi.

    N+1 bo'lmasin: 167 ta o'quvchi x 6 jadval = 1000 ta so'rov
    bo'lib ketardi. Har jadvalga bitta guruhlangan so'rov."""
    out: dict = {i: [] for i in ids}
    charges: dict = {i: 0 for i in ids}
    if not ids:
        return out, charges
    tables = {t.name: t for t in models.Base.metadata.sorted_tables}

    # 1) To'lovlar — TURI bilan
    pt = tables.get("payments")
    if pt is not None and "student_id" in pt.columns:
        col = pt.columns["student_id"]
        try:
            rows = db.execute(
                sa_select(col, pt.columns["kind"], sa_func.count())
                .where(col.in_(ids)).group_by(col, pt.columns["kind"])).all()
        except Exception:
            db.rollback()
            rows = []
        for sid, kind, n in rows:
            if sid not in out or not n:
                continue
            if (kind or "") == "charge":
                charges[sid] = charges.get(sid, 0) + n
            else:
                nom = {"payment": "to'lov", "discount": "chegirma",
                       "refund": "qaytarish"}.get(kind or "", kind or "yozuv")
                out[sid].append(f"{nom}: {n}")

    # 2) Qolgan jadvallar
    for tname, label in _ACTIVITY_TABLES:
        t = tables.get(tname)
        if t is None or "student_id" not in t.columns:
            continue
        col = t.columns["student_id"]
        try:
            rows = db.execute(
                sa_select(col, sa_func.count()).where(col.in_(ids))
                .group_by(col)).all()
        except Exception:
            db.rollback()
            continue
        for sid, n in rows:
            if sid in out and n:
                out[sid].append(f"{label}: {n}")
    return out, charges


# DIQQAT — YO'L NOMI. "/api/students/import-batches" BO'LMAYDI:
# GET /api/students/{student_id} faylda yuqoriroqda turibdi va
# "import-batches" ni o'quvchi raqami deb qabul qilib oladi (test
# aynan shuni tutdi). Shuning uchun alohida nom.
@router.get("/api/student-imports")
def import_batches(db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Oxirgi importlar ro'yxati — auditdan o'qiladi."""
    rows = (db.query(models.AuditLog)
            .filter(models.AuditLog.entity == "student",
                    models.AuditLog.action == "import")
            .order_by(models.AuditLog.id.desc()).limit(30).all())

    # GURUHNI SHU YERDA TOPAMIZ. Auditda guruh raqami saqlanmagan
    # (yorliq "Elena rus tili: 167 ta o'quvchi" ko'rinishida), lekin
    # brauzerga raqam kerak. Nom bo'yicha topib beramiz — shunda
    # oyna guruhlar ro'yxatisiz ham ishlaydi (2026-08-28, Jahongir:
    # "tanlab bo'lmayabdi" — ro'yxat bo'sh kelgan edi).
    by_name = {}
    for g in db.query(models.Group).all():
        by_name.setdefault((g.name or "").strip().lower(), g)

    out = []
    for a in rows:
        nom = str(a.entity_label or "").split(":")[0].strip()
        g = (db.query(models.Group).get(a.entity_id)
             if a.entity_id else None) or by_name.get(nom.lower())
        if g is not None and not _in_user_branches(db, user, g.branch_id,
                                                   null_ok=True):
            continue                      # boshqa filial — ko'rsatilmaydi
        out.append({
            "id": a.id,
            "label": a.entity_label,
            "count": a.new_value,
            "who": a.user_name,
            "at": a.created_at.isoformat() if a.created_at else None,
            "branch_id": getattr(a, "branch_id", None),
            "group_id": g.id if g is not None else None,
            "group": g.name if g is not None else nom,
        })
    return {"rows": out}


@router.post("/api/students/import-undo")
def import_undo(payload: dict = Body(...),
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.FREEZE_ROLES))):
    """{group_id, ids?, mode: "archive"|"delete", dry_run}

    dry_run (standart) — HECH NARSAGA TEGMAYDI, faqat ro'yxat.
    """
    gid = payload.get("group_id")
    g = db.query(models.Group).get(int(gid)) if gid else None
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if not _in_user_branches(db, user, g.branch_id, null_ok=True):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")

    mode = str(payload.get("mode") or "archive")
    dry = payload.get("dry_run", True)
    only = payload.get("ids")
    only = {int(x) for x in only} if only else None

    rows = db.query(models.Student).filter(in_group(g.id)).all()
    act, charges = _student_activity(db, [s.id for s in rows])

    free, kept = [], []
    for s in rows:
        item = {
            "id": s.id,
            "public_id": s.public_id,
            "name": s.full_name,
            "phone": s.phone,
            "status": s.status,
            "enrolled_date": (s.enrolled_date.isoformat()
                              if s.enrolled_date else None),
            "activity": act.get(s.id) or [],
            "charges": charges.get(s.id, 0),
            "balance": student_balance(db, s.id),
        }
        (kept if item["activity"] else free).append(item)

    if dry:
        qarz = round(sum(x["balance"] for x in free if x["balance"] < 0), 0)
        return {
            "dry_run": True,
            "group": g.name,
            "group_id": g.id,
            "branch_id": g.branch_id,
            "total": len(rows),
            "can_undo": len(free),
            "protected": len(kept),
            # XATO IMPORT PULGA HAM TEGADI: tizim har bir yangi
            "charges": sum(x["charges"] for x in free),
            "fake_debt": qarz,
            "rows": free,
            "protected_rows": kept,
            "hint": ("Tarixi bor o'quvchilar (to'lov, yo'qlama, coin, "
                     "imtihon) TEGILMAYDI — ular haqiqiy bo'lishi "
                     "mumkin. Tizim o'zi yozgan oylik hisob esa iz "
                     "hisoblanmaydi va o'quvchi bilan birga tozalanadi."),
        }

    # ---- HAQIQIY BAJARISH ----
    if mode == "delete" and user.role != roles.FOUNDER:
        raise HTTPException(403, "Butunlay o'chirish faqat asoschida. "
                                 "Arxivga o'tkazish esa sizda ochiq.")
    if only:
        # Server O'ZI tanlamaydi: tasdiqlanmagan ID qabul qilinmaydi.
        #
        # Bu tekshiruv TANLOVDAN OLDIN turishi shart. Aks holda
        # himoyalangan o'quvchi berilganda "hech kim tanlanmadi"
        # degan tushunarsiz javob chiqardi — nima uchun rad
        # etilgani bilinmasdi (test shuni tutdi).
        himoya = {x["id"]: x["name"] for x in kept}
        yomon = only - {x["id"] for x in free}
        if yomon:
            kim = [himoya[i] for i in list(yomon)[:3] if i in himoya]
            nega = ("tarixi bor (to'lov/yo'qlama/coin)" if kim
                    else "bu guruhda emas")
            raise HTTPException(
                400, f"{len(yomon)} ta o'quvchi bekor qilinmaydi — {nega}"
                     + (": " + ", ".join(kim) if kim else "")
                     + ". Ular haqiqiy o'quvchi bo'lishi mumkin.")
    target = [x for x in free if only is None or x["id"] in only]
    if not target:
        raise HTTPException(400, "Bekor qilinadigan o'quvchi tanlanmadi")

    today = roles.local_today()
    done, removed_all = 0, {}
    for x in target:
        s = db.query(models.Student).get(x["id"])
        if s is None:
            continue
        if mode == "delete":
            rem = _purge_student_children(db, s.id)
            for k, v in rem.items():
                removed_all[k] = removed_all.get(k, 0) + v
            db.delete(s)
        else:
            # ARXIVGA. Hech narsa yo'qolmaydi — qaytarib bo'ladi.
            #
            # LEKIN AVTOMAT HISOB (charge) OLIB TASHLANADI. Aks holda
            # arxivdagi 167 ta soxta o'quvchi filialning qarzida
            # turib qolardi va moliya raqami buzilardi. Bu odam
            # yozgan yozuv emas — tizim o'zi qo'ygan hisob.
            n_ch = db.query(models.Payment).filter(
                models.Payment.student_id == s.id,
                models.Payment.kind == "charge").delete(
                synchronize_session=False)
            if n_ch:
                removed_all["hisob (charge)"] = \
                    removed_all.get("hisob (charge)", 0) + n_ch
            s.status = "archived"
            s.left_date = s.left_date or today
            s.group_id = None
            s.note = ((s.note + " · ") if s.note else "")                 + f"Xato import — bekor qilindi ({today.isoformat()})"
            db.query(models.StudentGroupLink).filter(
                models.StudentGroupLink.student_id == s.id,
                models.StudentGroupLink.group_id == g.id).update(
                {"active": 0})
        done += 1

    detail = ", ".join(f"{k}:{v}" for k, v in sorted(removed_all.items()))
    audit.log(db, user, entity="student", action="import_undo",
              entity_label=f"{g.name}: {done} ta o'quvchi",
              new_value=done, branch_id=g.branch_id,
              old_value=("butunlay o'chirildi" if mode == "delete"
                         else "arxivga o'tkazildi")
                        + (f" ({detail})" if detail else ""),
              note="; ".join(f"{x['public_id'] or x['id']} {x['name']}"
                             for x in target[:200]))
    db.commit()
    return {"ok": True, "mode": mode, "done": done,
            "protected": len(kept), "removed": removed_all}


@router.post("/api/students/import")
def import_students(payload: schemas.StudentImportIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FREEZE_ROLES))):
    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if not _in_user_branches(db, user, g.branch_id, null_ok=True):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")

    today = roles.local_today()
    existing = db.query(models.Student).filter(
        in_group(g.id)).all()
    names = {(s.full_name or "").strip().lower() for s in existing}

    def _status(txt):
        t = (txt or "").strip().lower()
        if "arxiv" in t or "archiv" in t:
            return "archived"
        if "muzlat" in t or "frozen" in t:
            return "frozen"
        if "sinov" in t or "trial" in t:
            return "trial"
        return "active"

    results, created = [], 0
    for r in payload.rows:
        name = (r.full_name or "").strip()
        if not name:
            continue
        if name.lower() in names:
            results.append({"name": name, "status": "skip",
                            "reason": "bu guruhda allaqachon bor"})
            continue
        # DIQQAT: telefon bo'yicha o'tkazib yubormaymiz — aka-uka/opa-
        # singillar bitta (ota-onaning) raqami bilan yoziladi. Haqiqiy
        # dublikatni ism tekshiruvi ushlaydi.

        # LC UP bo'sh tug'ilgan sanaga eksport kunini yozadi — 4
        # yoshdan kichik chiqsa, sana yo'q deb hisoblaymiz.
        bdate = None
        if r.birth_date:
            try:
                bdate = date.fromisoformat(str(r.birth_date)[:10])
                if bdate.year > today.year - 4:
                    bdate = None
            except ValueError:
                bdate = None

        s = models.Student(
            full_name=name,
            phone=(r.phone or "").strip() or None,
            address=(r.address or "").strip() or None,
            birth_date=bdate,
            group_id=g.id,
            branch_id=g.branch_id,
            status=_status(r.status),
            subject=g.subject,
            level=g.level,
            enrolled_date=today,
        )
        db.add(s)
        names.add(name.lower())
        created += 1
        results.append({"name": name, "status": "ok"})
    db.commit()
    audit.log(db, user, entity="student", action="import",
              # entity_id — GURUH raqami. Keyin "importni bekor qilish"
              # oynasi guruhni nom bo'yicha izlamasin (2026-08-28).
              entity_id=g.id,
              entity_label=f"{g.name}: {created} ta o'quvchi",
              new_value=created, branch_id=g.branch_id, commit=True)
    return {"created": created, "group": g.name, "results": results}

