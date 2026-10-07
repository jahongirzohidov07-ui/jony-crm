"""JonyOS qo'shimcha moduli.

main.py juda katta bo'lib GitHub orqali yangilash vaqtincha imkonsiz
bo'lganda, YANGI endpointlar shu yerda ulanadi. Vercel /api so'rovlarni
shu faylga yo'naltiradi; u main.app ni olib, ustiga qo'shimchalarni
qo'shadi. main.py to'liq yangilanganda bu modul dublikatlarni olib
tashlab, o'z nusxasini qayta o'rnatadi — ikkala holatda ham bir xil
ishlaydi (idempotent).
"""
import os
import sys

# Vercel entry.py ni to'g'ridan-to'g'ri yuklaydi — api/ papkasini
# import yo'liga qo'shmasa, yonidagi modullar (audit, models...) topilmaydi.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
#  BU FAYL IKKI MARTA BAJARILMASIN (2026-09-21 — AVARIYA)
#
#  Vercel entry.py ni O'ZI qo'ygan modul nomi bilan yuklaydi (masalan
#  "vc_handler"), "entry" nomi bilan emas. Keyinroq, so'rov paytida
#  finance.py ichidagi `import entry as _E` ishga tushsa, Python uni
#  sys.modules da TOPOLMAYDI va butun faylni IKKINCHI marta
#  bajaradi — o'sha bitta `app` ustiga hamma route qayta o'raladi.
#
#  Natijasi bugun ko'rindi: /api/groups/{id}/attendance ikki qavat
#  o'ralib qoldi. Tashqi qavat ichkisini chaqiradi, ichkisi esa
#  oddiy dict qaytaradi (Pydantic model emas) — va yo'qlama
#  sahifasi hamma guruhda 500 bera boshladi. Ustozlar yo'qlama
#  qo'ya olmadi.
#
#  Yechim: modulni O'ZI "entry" nomi bilan ham ro'yxatga qo'yadi.
#  Shunda keyingi `import entry` tayyor nusxani oladi va fayl
#  qayta bajarilmaydi. Agar Python allaqachon "entry" deb yuklagan
#  bo'lsa, setdefault hech narsani o'zgartirmaydi.
# =====================================================================
sys.modules.setdefault("entry", sys.modules[__name__])

from datetime import date

from fastapi import Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import models
import roles
import schemas
from main import (  # noqa: F401
    app, get_db, require_role, scope_to_branch, _get_group_in_scope,
    _my_teacher_or_404, get_current_user,
)
from common import ensure_tables  # noqa: E402
import main as M
import common as _C


def _drop_route(path: str, method: str) -> None:
    """Bir xil yo'l qayta e'lon qilinganda eskisini olib tashlaydi —
    main.py yangi versiyada bo'lsa ham, bo'lmasa ham bitta nusxa qoladi.

    2026-08: main.py bo'lindi - domen routerlari endi
    app.include_router(...) orqali ulanadi, shuning uchun
    app.router.routes ichida to'g'ridan-to'g'ri emas, balki
    _IncludedRouter ichiga o'ralgan holda turadi. Shu ichkariga
    ham qarab, mos yo'lni topib olib tashlaymiz - xatti-harakat
    o'zgarmagan, faqat qidiruv chuqurroq."""
    def _matches(r):
        return getattr(r, "path", None) == path and \
            method in (getattr(r, "methods", None) or [])

    keep = []
    for r in app.router.routes:
        if _matches(r):
            continue
        ic = getattr(r, "include_context", None)
        nested = getattr(ic, "included_router", None) if ic else None
        if nested is not None and hasattr(nested, "routes"):
            nested.routes = [nr for nr in nested.routes if not _matches(nr)]
        keep.append(r)
    app.router.routes = keep


# HR menejerga "rahbariyat" sifatida dars ko'chirishni tasdiqlash/
# ko'rish huquqi shu YERDA, faylning ENG BOSHIDA berilishi SHART.
# Sabab: pastroqda (~qator 3040) xuddi shu qo'shimcha bor edi, lekin u
# YETARLI EMAS - Python fayl ichidagi @decorator'larni YUQORIDAN
# PASTGA, YOZUV TARTIBIDA ishga tushiradi va require_role(*ro'yxat)
# ro'yxatni SHU DAQIQADAGI holatida (snapshot) o'qib oladi, keyin
# ro'yxat o'zgarsa ham bu qayta o'qilmaydi. Natijada pastroqdagi
# qo'shimcha faylning YUQORI qismidagi reschedule_decide_v2 (~qator
# 1170) uchun umuman kech qolar edi, GET /api/reschedules
# (groups_lessons.py, main.py orqali - bu esa entry.py o'zining birinchi
# qatoridayoq to'liq import qilib bo'ladi) uchun esa HECH QACHON
# yetib bormas edi - u fayl entry.py ishga tushishidan OLDIN to'liq
# yuklanib bo'ladi. Amalda: HR menejer darsni TO'G'RIDAN-TO'G'RI
# ko'chira olardi (bu tekshiruv unga bog'liq emas edi), lekin
# ustozning kvotadan oshgan so'rovlarini KO'RA ("Bu amal uchun
# ruxsatingiz yo'q") ham, TASDIQLAY ham OLMASDI.
if roles.HR_MANAGER not in roles.RESCHEDULE_APPROVE:
    roles.RESCHEDULE_APPROVE.append(roles.HR_MANAGER)


# =====================================================================
#  MASHQLAR — natijalar, ballar va daraja zinasi
# =====================================================================
def _practice_summary(db: Session, student_id: int) -> dict:
    rows = (db.query(func.count(models.ExerciseResult.id),
                     func.coalesce(func.sum(models.ExerciseResult.total), 0),
                     func.coalesce(func.sum(models.ExerciseResult.correct), 0))
            .filter(models.ExerciseResult.student_id == student_id).one())
    done, total, correct = int(rows[0]), int(rows[1]), int(rows[2])
    # 2026-08-25: zina chiziqli emas (roles.ENG_LEVEL_POINTS)
    idx = roles.level_index_for(correct)
    cur = roles.ENG_LEVELS[idx]
    is_last = idx >= len(roles.ENG_LEVELS) - 1
    nxt = None if is_last else roles.ENG_LEVELS[idx + 1]
    lo = cur["need"]
    per = max(1, (nxt["need"] if nxt else lo) - lo)
    in_level = correct - lo
    return {
        "done": done, "total": total, "correct": correct,
        "percent": round(correct * 100 / total, 1) if total else 0,
        "points": correct,
        "level": cur,
        "next": None if is_last else {
            "label": nxt["label"], "ielts": nxt["ielts"],
            "cefr": nxt["cefr"],
            "points_left": per - in_level,
            "progress_percent": round(in_level * 100 / per, 1),
        },
        "levels": roles.ENG_LEVELS,
    }


_drop_route("/api/students/{student_id}/exercises", "GET")


@app.get("/api/students/{student_id}/exercises")
def student_exercises(student_id: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF,
                                                roles.HR_MANAGER))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rows = (db.query(models.ExerciseResult)
            .filter(models.ExerciseResult.student_id == student_id)
            .order_by(models.ExerciseResult.date.desc(),
                      models.ExerciseResult.id.desc())
            .limit(100).all())
    return {
        "summary": _practice_summary(db, student_id),
        "rows": [{
            "id": r.id,
            "date": r.date.isoformat() if r.date else None,
            "total": r.total, "correct": r.correct,
            "percent": round(r.correct * 100 / r.total, 1) if r.total else 0,
            "topic": r.topic, "created_by": r.created_by,
        } for r in rows],
    }


_drop_route("/api/students/{student_id}/exercises", "POST")


@app.post("/api/students/{student_id}/exercises")
def add_exercise(student_id: int, payload: schemas.ExerciseIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.TEACHING_ACCESS))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not (1 <= payload.total <= 500):
        raise HTTPException(400, "Savollar soni 1-500 oralig'ida bo'lsin")
    if not (0 <= payload.correct <= payload.total):
        raise HTTPException(400, "To'g'ri javoblar jami savoldan oshmaydi")
    before = _practice_summary(db, student_id)["level"]["key"]
    r = models.ExerciseResult(
        student_id=student_id, total=payload.total,
        correct=payload.correct,
        topic=(payload.topic or "").strip() or None,
        created_by=user.full_name)
    db.add(r)
    db.commit()
    after = _practice_summary(db, student_id)
    leveled_up = after["level"]["key"] != before
    if leveled_up:
        audit.log(db, user, entity="student", action="practice_level",
                  entity_id=s.id, entity_label=s.full_name,
                  new_value=after["level"]["label"],
                  note="Mashqlar bo'yicha yangi daraja",
                  branch_id=s.branch_id, commit=True)
    return {"ok": True, "summary": after, "leveled_up": leveled_up}


_drop_route("/api/exercises/{rid}", "DELETE")


@app.delete("/api/exercises/{rid}")
def delete_exercise(rid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FULL_ACCESS,
                                              roles.ACADEMIC_HEAD))):
    r = db.query(models.ExerciseResult).get(rid)
    if not r:
        raise HTTPException(404, "Yozuv topilmadi")
    db.delete(r)
    db.commit()
    return {"ok": True}


_drop_route("/api/groups/{group_id}/exercises-stats", "GET")


@app.get("/api/groups/{group_id}/exercises-stats")
def group_exercises_stats(group_id: int,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *roles.TEACHING_ACCESS, roles.HR_MANAGER))):
    g = _get_group_in_scope(db, group_id, user)
    students = (db.query(models.Student)
                .filter(models.Student.group_id == g.id,
                        models.Student.status.in_(("active", "trial")))
                .order_by(models.Student.full_name).all())
    rows = []
    for s in students:
        sm = _practice_summary(db, s.id)
        rows.append({
            "student_id": s.id, "full_name": s.full_name,
            "done": sm["done"], "percent": sm["percent"],
            "points": sm["points"], "level": sm["level"],
            "next": sm["next"],
        })
    return {"group": g.name, "rows": rows, "levels": roles.ENG_LEVELS}


# =====================================================================
#  GURUHLARDA SUPPORT KO'RINISHI
# =====================================================================
def _group_support_map(db: Session, group_ids: list) -> dict:
    if not group_ids:
        return {}
    rows = (db.query(models.SupportAssignment.group_id,
                     models.User.full_name)
            .join(models.User,
                  models.User.id == models.SupportAssignment.user_id)
            .filter(models.SupportAssignment.group_id.in_(group_ids),
                    models.User.is_active == 1,
                    # qo'shimcha lavozimi support bo'lganlar ham
                    # (2026-09-30)
                    _C._support_cond())
            .all())
    m = {}
    for gid, name in rows:
        m.setdefault(gid, []).append(name)
    return {gid: ", ".join(sorted(set(names)))
            for gid, names in m.items()}


_drop_route("/api/groups", "GET")


@app.get("/api/groups", response_model=list[schemas.GroupOut])
def list_groups(branch_id: int | None = None,
                archived: int = 0,
                db: Session = Depends(get_db),
                user=Depends(M.get_current_user)):
    M.backfill_missing_ids(db, "group", models.Group)
    q = scope_to_branch(db.query(models.Group), models.Group, user,
                        branch_id)
    # ARXIV (2026-09-30): sukut bo'yicha arxivdagi guruhlar ro'yxatda,
    # tanlagichlarda va jadvalda ko'rinmaydi; archived=1 — faqat
    # arxivdagilar (Arxiv bo'limi).
    q = q.filter(models.Group.archived_at.isnot(None) if archived
                 else models.Group.archived_at.is_(None))
    # TEZLIK (2026-08-15): ustoz va filial guruhlar bilan BIRGA
    # o'qiladi. Ilgari har guruh uchun alohida so'rov ketardi
    # (45 guruh = 21 ortiqcha so'rov). Javob o'zgarmaydi.
    from sqlalchemy.orm import selectinload as _sel
    groups = (q.options(_sel(models.Group.teacher),
                        _sel(models.Group.branch))
              .order_by(models.Group.name).all())
    counts = dict(
        db.query(models.Student.group_id, func.count(models.Student.id))
        .filter(models.Student.status == "active",
                models.Student.group_id.isnot(None))
        .group_by(models.Student.group_id).all())
    # MUZLATILGANLAR ALOHIDA (2026-09-08, Jahongir: "ichidagi
    # o'quvchini ochirib tashlasayam ochmayabdi"). Ular yuqoridagi
    # songa kirmaydi — shuning uchun guruh "[0]" ko'rinib turib
    # o'chirilmasdi va sababi ko'rinmasdi.
    frozen = dict(
        db.query(models.Student.group_id, func.count(models.Student.id))
        .filter(models.Student.status == "frozen",
                models.Student.group_id.isnot(None))
        .group_by(models.Student.group_id).all())
    sup_map = _group_support_map(db, [g.id for g in groups])
    out = []
    for g in groups:
        item = schemas.GroupOut.model_validate(g)
        item.student_count = counts.get(g.id, 0)
        item.frozen_count = frozen.get(g.id, 0)
        item.support_label = sup_map.get(g.id)
        out.append(item)
    return out


_drop_route("/api/groups/{group_id}", "GET")


@app.get("/api/groups/{group_id}", response_model=schemas.GroupOut)
def get_group(group_id: int, db: Session = Depends(get_db),
              user=Depends(M.get_current_user)):
    group = _get_group_in_scope(db, group_id, user)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = db.query(models.Student).filter(
        models.Student.group_id == group.id,
        models.Student.status == "active").count()
    item.support_label = _group_support_map(db, [group.id]).get(group.id)
    return item


# =====================================================================
#  SUPPORT SEANSI ASOSIY DARSGA TUSHMASIN
# =====================================================================
_drop_route("/api/me/support-sessions", "POST")


@app.post("/api/me/support-sessions")
def my_support_session_add(payload: schemas.SupportSessionIn,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               roles.SUPPORT_TEACHER,
                               *roles.PAST_ATTENDANCE))):
    t = _my_teacher_or_404(db, user) if user.role == roles.SUPPORT_TEACHER \
        else M._teacher_of_user(db, user)
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
    if s_min is None:
        raise HTTPException(400, "Vaqt SS:DD ko'rinishida bo'lsin, "
                                 "masalan 14:30")

    # SOAT: support qancha dars o'tganini O'ZI belgilaydi (2026-08-10).
    # Ikki xil kiritish qo'llab-quvvatlanadi — tayyor soat (1/1.5/2/
    # 2.5/3) yoki tugash vaqti. Soat berilsa tugash vaqti o'zi
    # hisoblanadi, shunda telefonda ortiqcha ish qolmaydi.
    if payload.hours is not None:
        try:
            hrs = float(payload.hours)
        except (TypeError, ValueError):
            raise HTTPException(400, "Soatni to'g'ri tanlang")
        minutes = int(round(hrs * 60))
        e_min = s_min + minutes
        end_time = f"{(e_min // 60) % 24:02d}:{e_min % 60:02d}"
    else:
        e_min = roles.hhmm_minutes(payload.end_time or "")
        if e_min is None:
            raise HTTPException(400, "Tugash vaqtini kiriting yoki "
                                     "necha soat dars o'tganingizni tanlang")
        if e_min <= s_min:
            raise HTTPException(400, "Tugash vaqti boshlanishdan keyin "
                                     "bo'lishi kerak")
        minutes = e_min - s_min
        end_time = payload.end_time.strip()

    # 1-3 SOAT QOIDASI (Jahongir belgiladi): kamida bir soat, ko'pi
    # bilan uch soat. Chegaradan chiqsa yozilmaydi — oylik shu
    # yozuvlardan hisoblanadi, shuning uchun qat'iy.
    if minutes < roles.SUPPORT_SESSION_MIN_HOURS * 60:
        raise HTTPException(
            400, f"Seans kamida {roles.SUPPORT_SESSION_MIN_HOURS} "
                 f"soat bo'lishi kerak")
    if minutes > roles.SUPPORT_SESSION_MAX_HOURS * 60:
        raise HTTPException(
            400, f"Bitta seans {roles.SUPPORT_SESSION_MAX_HOURS} "
                 f"soatdan oshmaydi")
    if not (1 <= payload.students_count
            <= roles.SUPPORT_SESSION_MAX_STUDENTS):
        raise HTTPException(
            400, f"O'quvchilar soni 1 dan "
                 f"{roles.SUPPORT_SESSION_MAX_STUDENTS} gacha")

    # ASOSIY DARS bilan to'qnashuv
    wd = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][d.weekday()]
    if wd in (g.lesson_days or "") and g.lesson_time \
            and "-" in g.lesson_time:
        gs, ge = g.lesson_time.split("-", 1)
        gs, ge = roles.hhmm_minutes(gs), roles.hhmm_minutes(ge)
        if gs is not None and ge is not None \
                and s_min < ge and gs < e_min:
            raise HTTPException(
                400, f"DIQQAT: bu vaqt \"{g.name}\" guruhining ASOSIY "
                     f"darsi bilan bir xil ({g.lesson_time}). Support "
                     f"seansi asosiy darsdan alohida vaqtda bo'ladi — "
                     f"vaqtni tekshirib qayta kiriting.")

    # Yakka darslar bu qoidaga kirmaydi (2026-09-23): shu guruhdagi
    # bitta o'quvchi bilan alohida shug'ullanish guruh seansini
    # yozishga to'sqinlik qilmasligi kerak.
    dup = (db.query(models.SupportSession)
           .filter(models.SupportSession.teacher_id == t.id,
                   models.SupportSession.group_id == g.id,
                   models.SupportSession.student_id.is_(None),
                   models.SupportSession.date == d).first())
    if dup:
        raise HTTPException(400, "Bu kunga bu guruh uchun seans "
                                 "allaqachon kiritilgan")

    row = models.SupportSession(
        teacher_id=t.id, group_id=g.id, branch_id=g.branch_id, date=d,
        start_time=payload.start_time.strip(),
        end_time=end_time,
        minutes=minutes,
        students_count=payload.students_count,
        note=(payload.note or "").strip() or None,
        # created_by — SON (users.id), ISM EMAS. 2026-09-06: bu yerda
        # user.full_name yozilardi va Postgres har safar xato berardi
        # ("invalid input syntax for type integer") — support soatini
        # SAQLAY OLMASDI (jonli xato jurnalida 12 marta, 8 xodimda).
        # me.py va yo'qlamadan avtomat yozuvda to'g'ri edi.
        created_by=user.id)
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id, "minutes": minutes}


# =====================================================================
#  OTA-ONA PORTALIDA MASHQ DARAJASI
#
#  MUHIM (2026-08-09 topildi): parents.py:parent_view() da qo'shilgan
#  parent_token_expires_at tekshiruvi shu YERGA — haqiqiy ishlaydigan
#  nusxaga — hech qachon ko'chirilmagan ekan. entry.py o'z ustidan
#  BUTUNLAY MUSTAQIL parent_view() yozadi (parents.py'nikini chaqirmay,
#  hammasini qaytadan yozadi) va _drop_route orqali uni almashtiradi —
#  demak parents.py'dagi muddat tekshiruvi HECH QACHON ishlamagan
#  (create_user_v2'da topilgan xuddi shu naqsh). Muddati o'tgan
#  havolalar shu paytgacha baribir ochilaverar edi. Endi shu yerga
#  ham qo'shildi — bu HAQIQIY jonli yo'l.
# =====================================================================
_drop_route("/api/parent/{token}", "GET")


# Ota-onaga ko'rsatiladigan yorliqlar — StudentDetail.tsx (KIND_LABEL)
# va src/lib/payments.ts (PAYMENT_METHODS) bilan bir xil so'zlar.
_PARENT_KIND_LABEL = {
    "payment": "To'lov", "charge": "Hisoblandi",
    "discount": "Chegirma", "refund": "Refund (qaytarildi)",
    "adjustment": "Balans tuzatildi",
}
_PARENT_METHOD_LABEL = {
    "cash": "Naqd", "card": "Click",
    "terminal": "Terminal", "other": "Boshqa",
}


@app.get("/api/parent/{token}")
def parent_view(token: str, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    from common import _gam_card, _xp_history, _student_ranks
    if not token or len(token) < 10:
        raise HTTPException(404, "Topilmadi")
    s = db.query(models.Student).filter(
        models.Student.parent_token == token).first()
    if not s:
        raise HTTPException(404, "Topilmadi")
    if (s.parent_token_expires_at
            and s.parent_token_expires_at < datetime.utcnow()):
        raise HTTPException(
            404, "Havola muddati tugagan. Administratordan yangi "
                 "havola so'rang.")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    today = roles.local_today()
    start = today - timedelta(days=45)
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson,
                  models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == s.id,
                    models.Lesson.date >= start,
                    models.Lesson.date <= today)
            .order_by(models.Lesson.date.desc()).limit(24).all())
    att = [{
        "date": ls.date.isoformat(),
        "present": int(a.present or 0),
        "homework": a.homework,
    } for a, ls in rows]
    bal = M.student_balance(db, s.id)
    st_lbl = {"active": "faol", "trial": "sinovda",
              "frozen": "muzlatilgan", "archived": "arxivda"}

    # TO'LOVLAR TARIXI, COIN/XP, O'ZLASHTIRISH VA TEST NATIJALARI
    # (2026-08-09, Jahongir so'radi): avval faqat davomat va jami
    # balans ko'rinardi. MUHIM: bu funksiya haqiqiy jonli yo'l
    # (yuqoridagi izohga qarang — parents.py'dagi nusxa umuman
    # ishlamaydi), shuning uchun yangi qism aynan SHU YERGA
    # qo'shildi. Barchasi faqat shu bitta o'quvchi (s.id) bilan
    # cheklangan.
    pay_rows = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id)
                .order_by(models.Payment.created_at.desc())
                .limit(30).all())
    payments = [{
        "date": p.created_at.isoformat() if p.created_at else None,
        "amount": p.amount,
        "kind": _PARENT_KIND_LABEL.get(p.kind, p.kind),
        "method": (_PARENT_METHOD_LABEL.get(p.method, p.method)
                  if p.method else None),
        "note": p.note,
    } for p in pay_rows]

    gam = _gam_card(db, s)
    xp_history = [{
        "date": h["date"],
        "amount": h["amount"],
        "label": h["label"],
        "category_label": h["category_label"],
        "tone": h["tone"],
    } for h in _xp_history(db, s.id, limit=15)]

    grade_rows = (db.query(models.DailyGrade, models.Lesson)
                  .join(models.Lesson,
                        models.DailyGrade.lesson_id == models.Lesson.id)
                  .filter(models.DailyGrade.student_id == s.id)
                  .order_by(models.Lesson.date.desc()).limit(20).all())
    daily_grades = [{
        "date": ls.date.isoformat(),
        "score": dg.score,
    } for dg, ls in grade_rows]

    # Faqat TASDIQLANGAN yoki NATIJA KIRITILGAN testlar ko'rinsin —
    # qoralama (draft, hali Examiner tasdiqlamagan) va bekor qilingan
    # ko'rinmasin. TUZATILDI (2026-08-09): ilgari faqat "approved"
    # o'tkazilardi, lekin save_exam_results() natija kiritilgach
    # statusni "done"ga o'zgartiradi (exams.py) — demak haqiqiy
    # kiritilgan natijalar aynan shu holatga o'tgach ko'rinmay
    # qolardi. Endi ikkalasi ham hisobga olinadi.
    exam_rows = (db.query(models.ExamResult, models.Exam)
                 .join(models.Exam,
                       models.ExamResult.exam_id == models.Exam.id)
                 .filter(models.ExamResult.student_id == s.id,
                         models.Exam.status.in_(["approved", "done"]))
                 .order_by(models.Exam.date.desc()).limit(20).all())
    exam_results = [{
        "date": ex.date.isoformat() if ex.date else None,
        "title": ex.title or roles.exam_title(ex.kind, ex.unit_no),
        "score": er.score,
        "max_score": ex.max_score,
        "band": er.band,
        "percent": er.percent,
        "absent": bool(er.absent),
    } for er, ex in exam_rows]

    return {
        "name": s.full_name,
        "group": g.name if g else None,
        "lesson_time": g.lesson_time if g else None,
        "status": st_lbl.get(s.status, s.status),
        "balance": bal,
        "attendance": att,
        "frozen_until": s.frozen_until.isoformat()
        if s.frozen_until else None,
        "practice": _practice_summary(db, s.id),
        "payments": payments,
        "gamification": gam,
        "xp_history": xp_history,
        "daily_grades": daily_grades,
        "exam_results": exam_results,
        "ranks": _student_ranks(db, s.id),
    }

# =====================================================================
#  SUPPORT JADVALIDA GURUHGA O'TISH — bloklarda group_id
# =====================================================================
_drop_route("/api/support-timetable", "GET")


@app.get("/api/support-timetable")
def support_timetable(day: str = "mon",
                      branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(
                          *roles.FULL_ACCESS, roles.HEAD_SUPPORT,
                          roles.ACADEMIC_HEAD, roles.HR_MANAGER))):
    """Supportlar jadvali: guruh bloki bosilganda guruhga kirish uchun
    group_id ham qaytadi."""
    if day not in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        raise HTTPException(400, "Kun noto'g'ri")
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.User.role == roles.SUPPORT_TEACHER,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = []
    for t in q.order_by(models.Teacher.full_name).all():
        blocks = []
        gids = [a.group_id for a in
                db.query(models.SupportAssignment)
                .filter(models.SupportAssignment.user_id == t.user_id,
                        models.SupportAssignment.group_id.isnot(None))
                .all()]
        for g in (db.query(models.Group)
                  .filter(models.Group.id.in_(gids or [-1])).all()):
            if day not in (g.lesson_days or ""):
                continue
            st = (g.lesson_time or "").split("-")[0].strip()
            blocks.append({
                "kind": "group", "label": g.name,
                "group_id": g.id,
                "time": g.lesson_time or "",
                "sort": M._time_to_min(st) or 0,
                "room": g.room,
            })
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            if day not in (b.days or ""):
                continue
            blocks.append({
                "kind": "busy",
                "label": b.note or "Band (o'zi belgilagan)",
                "time": f"{b.start}-{b.end}",
                "sort": M._time_to_min(b.start) or 0,
            })
        blocks.sort(key=lambda x: x["sort"])
        rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": bnames.get(t.branch_id),
            "blocks": blocks,
        })
    return {"day": day, "rows": rows}

# =====================================================================
#  RO'YXATDAN TURIB SUPPORT BIRIKTIRISH / USTOZ ALMASHTIRISH
#  Guruh kartasiga kirmasdan, Guruhlar ro'yxatining o'zida.
# =====================================================================
from pydantic import BaseModel as _BM


class _GroupSupportsIn(_BM):
    user_ids: list[int] = []


_drop_route("/api/groups/{group_id}/supports", "GET")


@app.get("/api/groups/{group_id}/supports")
def group_supports(group_id: int,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    """Guruhga biriktirilgan supportlar + tanlash uchun ro'yxat."""
    g = _get_group_in_scope(db, group_id, user)
    assigned = [a.user_id for a in
                db.query(models.SupportAssignment)
                .filter(models.SupportAssignment.group_id == g.id).all()]
    q = (db.query(models.Teacher, models.User)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.User.role == roles.SUPPORT_TEACHER,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    options = [{
        "user_id": t.user_id, "name": t.full_name,
        "branch": bnames.get(t.branch_id),
    } for t, u in q.order_by(models.Teacher.full_name).all()]
    return {"assigned": assigned, "options": options}


_drop_route("/api/groups/{group_id}/supports", "PUT")


@app.put("/api/groups/{group_id}/supports")
def set_group_supports(group_id: int, payload: _GroupSupportsIn,
                       force: bool = False,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    """Guruh uchun supportlar to'plamini saqlash. Yangi support
    qo'shilsa unga xabar boradi; band vaqtiga to'qnashsa 409
    ogohlantirish qaytadi (force=true bilan o'tkaziladi)."""
    g = _get_group_in_scope(db, group_id, user)
    want = set(payload.user_ids or [])
    for uid in want:
        u = db.query(models.User).get(uid)
        if not u or u.role != roles.SUPPORT_TEACHER:
            raise HTTPException(400, "Faqat support teacherlarni "
                                     "biriktirish mumkin")
    cur = {a.user_id: a for a in
           db.query(models.SupportAssignment)
           .filter(models.SupportAssignment.group_id == g.id).all()}
    added = sorted(want - set(cur))
    removed = sorted(set(cur) - want)
    if added and not force and hasattr(M, "_support_conflicts"):
        warns = []
        for uid in added:
            t = (db.query(models.Teacher)
                 .filter(models.Teacher.user_id == uid,
                         models.Teacher.is_active == 1).first())
            if t is not None:
                warns += M._support_conflicts(db, t.id, [g])
        if warns:
            raise HTTPException(409, " • ".join(warns[:3]))
    for uid in removed:
        db.delete(cur[uid])
    for uid in added:
        db.add(models.SupportAssignment(
            user_id=uid, group_id=g.id, created_by=user.full_name))
        days = M._days_uz(g.lesson_days) if hasattr(M, "_days_uz") \
            else (g.lesson_days or "")
        M._hr_task_for(
            db, uid,
            title=f"Sizga guruh biriktirildi: {g.name}",
            body=(f"\"{g.name}\" guruhi ({days} {g.lesson_time or ''}) "
                  f"sizga support sifatida biriktirildi."),
            branch_id=g.branch_id)
    db.commit()
    label = _group_support_map(db, [g.id]).get(g.id)
    return {"ok": True, "support_label": label,
            "added": len(added), "removed": len(removed)}

# =====================================================================
#  SUPPORT VAQTLARI + TELEFON-LOGIN
#  1) Biriktirishda support darsining KUN/VAQTI so'raladi va saqlanadi.
#  2) Jadval asosiy dars vaqtini EMAS, shu belgilangan vaqtni ko'rsatadi.
#  3) Yangi akkaunt: telefon majburiy, login = raqam, parol = jonyjony.
# =====================================================================
import re as _re

from sqlalchemy import inspect as _sa_inspect, text as _sa_text

from auth import hash_password as _hash_pw
from auth import has_role as _has_role, is_partner_head as _is_ph
from database import engine as _engine

# --- support_assignments jadvaliga ustunlar (idempotent ALTER) ---
try:
    _cols = {c["name"] for c in
             _sa_inspect(_engine).get_columns("support_assignments")}
    with _engine.begin() as _c:
        if "days" not in _cols:
            _c.execute(_sa_text(
                "ALTER TABLE support_assignments ADD COLUMN days VARCHAR"))
        if "start" not in _cols:
            _c.execute(_sa_text(
                "ALTER TABLE support_assignments ADD COLUMN start VARCHAR"))
        if "end" not in _cols:
            _c.execute(_sa_text(
                'ALTER TABLE support_assignments ADD COLUMN "end" VARCHAR'))
except Exception:
    pass


class _SupItem(_BM):
    user_id: int
    days: str | None = None      # "mon,wed"
    start: str | None = None     # "14:00"
    end: str | None = None       # "16:00"


class _GroupSupportsIn2(_BM):
    items: list[_SupItem] | None = None
    user_ids: list[int] | None = None  # eski format ham qabul qilinadi


def _sup_time_ok(it) -> str | None:
    """Vaqt kiritilgan bo'lsa to'g'riligini tekshiradi."""
    if not (it.days or it.start or it.end):
        return None
    if not (it.days and it.start and it.end):
        return "Kun va vaqtni to'liq kiriting (yoki butunlay bo'sh qoldiring)"
    s, e = roles.hhmm_minutes(it.start), roles.hhmm_minutes(it.end)
    if s is None or e is None:
        return "Vaqt SS:DD ko'rinishida bo'lsin, masalan 14:00"
    if e <= s:
        return "Tugash vaqti boshlanishdan keyin bo'lsin"
    return None


def _sup_conflicts2(db: Session, uid: int, it, skip_group_id: int) -> list:
    """Yangi belgilangan vaqt supportning band vaqtlari yoki boshqa
    guruhlardagi BELGILANGAN vaqtlari bilan to'qnashsa — ro'yxat."""
    if not (it.days and it.start and it.end):
        return []
    days = set((it.days or "").split(","))
    s, e = roles.hhmm_minutes(it.start), roles.hhmm_minutes(it.end)
    out = []
    t = (db.query(models.Teacher)
         .filter(models.Teacher.user_id == uid,
                 models.Teacher.is_active == 1).first())
    if t is not None:
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            bs, be = roles.hhmm_minutes(b.start), roles.hhmm_minutes(b.end)
            if bs is None or be is None:
                continue
            if days & set((b.days or "").split(",")) and s < be and bs < e:
                out.append(f"Support bu vaqtni BAND deb belgilagan: "
                           f"{b.start}-{b.end} ({b.note or 'sabab yozilmagan'})")
    rows = (db.query(models.SupportAssignment, models.Group)
            .join(models.Group,
                  models.Group.id == models.SupportAssignment.group_id)
            .filter(models.SupportAssignment.user_id == uid,
                    models.SupportAssignment.group_id != skip_group_id)
            .all())
    for a, g in rows:
        if not (a.days and a.start and a.end):
            continue
        os_, oe = roles.hhmm_minutes(a.start), roles.hhmm_minutes(a.end)
        if os_ is None or oe is None:
            continue
        if days & set((a.days or "").split(",")) and s < oe and os_ < e:
            out.append(f"\"{g.name}\" guruhida allaqachon band: "
                       f"{a.start}-{a.end}")
    return out


_drop_route("/api/groups/{group_id}/supports", "GET")


@app.get("/api/groups/{group_id}/supports")
def group_supports_v2(group_id: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    g = _get_group_in_scope(db, group_id, user)
    assigned = [{
        "user_id": a.user_id, "days": a.days,
        "start": a.start, "end": a.end,
    } for a in db.query(models.SupportAssignment)
        .filter(models.SupportAssignment.group_id == g.id).all()]
    # Qo'shimcha lavozimi support bo'lganlar ham (2026-09-30)
    _C._ensure_support_cards(db)
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(_C._support_cond(), models.User.is_active == 1,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    options = [{
        "user_id": t.user_id, "name": t.full_name,
        "branch": bnames.get(t.branch_id),
    } for t in q.order_by(models.Teacher.full_name).all()]
    return {"assigned": assigned, "options": options}


_drop_route("/api/groups/{group_id}/supports", "PUT")


@app.put("/api/groups/{group_id}/supports")
def set_group_supports_v2(group_id: int, payload: _GroupSupportsIn2,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    g = _get_group_in_scope(db, group_id, user)
    items = payload.items
    if items is None:
        items = [_SupItem(user_id=u) for u in (payload.user_ids or [])]
    seen = set()
    for it in items:
        if it.user_id in seen:
            raise HTTPException(400, "Bitta support ikki marta tanlangan")
        seen.add(it.user_id)
        u = db.query(models.User).get(it.user_id)
        if not u or not _C._is_support_user(db, u):
            raise HTTPException(400, "Faqat support teacherlarni "
                                     "biriktirish mumkin")
        msg = _sup_time_ok(it)
        if msg:
            raise HTTPException(400, msg)
    if not force:
        warns = []
        for it in items:
            warns += _sup_conflicts2(db, it.user_id, it, g.id)
        if warns:
            raise HTTPException(409, " \u2022 ".join(warns[:3]))
    cur = {a.user_id: a for a in
           db.query(models.SupportAssignment)
           .filter(models.SupportAssignment.group_id == g.id).all()}
    want = {it.user_id: it for it in items}
    added = []
    for uid, a in list(cur.items()):
        if uid not in want:
            db.delete(a)
    for uid, it in want.items():
        if uid in cur:
            a = cur[uid]
            a.days, a.start, a.end = it.days, it.start, it.end
        else:
            db.add(models.SupportAssignment(
                user_id=uid, group_id=g.id,
                days=it.days, start=it.start, end=it.end,
                created_by=user.full_name))
            added.append((uid, it))
    for uid, it in added:
        vaqt = f"{it.days or ''} {it.start or ''}-{it.end or ''}".strip(" -")
        M._hr_task_for(
            db, uid,
            title=f"Sizga guruh biriktirildi: {g.name}",
            body=(f"\"{g.name}\" guruhi sizga support sifatida "
                  f"biriktirildi. Dars vaqti: {vaqt or 'kelishiladi'}."),
            branch_id=g.branch_id)
    db.commit()
    label = _group_support_map(db, [g.id]).get(g.id)
    return {"ok": True, "support_label": label}


_drop_route("/api/support-timetable", "GET")


@app.get("/api/support-timetable")
def support_timetable_v2(day: str = "mon",
                         branch_id: int | None = None,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(
                             *roles.FULL_ACCESS, roles.HEAD_SUPPORT,
                             roles.ACADEMIC_HEAD, roles.HR_MANAGER))):
    """Supportlar jadvali. MUHIM: guruhning ASOSIY dars vaqti emas,
    biriktirishda BELGILANGAN support-dars vaqti ko'rsatiladi."""
    if day not in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        raise HTTPException(400, "Kun noto'g'ri")
    # Qo'shimcha lavozimi support bo'lganlar ham (2026-09-30)
    _C._ensure_support_cards(db)
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(_C._support_cond(), models.User.is_active == 1,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = []
    for t in q.order_by(models.Teacher.full_name).all():
        blocks = []
        arows = (db.query(models.SupportAssignment, models.Group)
                 .join(models.Group,
                       models.Group.id == models.SupportAssignment.group_id)
                 .filter(models.SupportAssignment.user_id == t.user_id)
                 .all())
        for a, g in arows:
            if not (a.days and a.start and a.end):
                continue  # vaqti hali belgilanmagan
            if day not in (a.days or ""):
                continue
            blocks.append({
                "kind": "group", "label": g.name,
                "group_id": g.id,
                "time": f"{a.start}-{a.end}",
                "sort": roles.hhmm_minutes(a.start) or 0,
                "room": g.room,
            })
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            if day not in (b.days or ""):
                continue
            blocks.append({
                "kind": "busy",
                "label": b.note or "Band (o'zi belgilagan)",
                "time": f"{b.start}-{b.end}",
                "sort": roles.hhmm_minutes(b.start) or 0,
            })
        blocks.sort(key=lambda x: x["sort"])
        rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": bnames.get(t.branch_id),
            "blocks": blocks,
        })
    return {"day": day, "rows": rows}


# --------------------------------------------------------------
#  YANGI AKKAUNT: telefon majburiy, login = raqam, parol jonyjony
# --------------------------------------------------------------
class _UserCreate2(schemas.UserCreate):
    username: str | None = None
    password: str | None = None


_drop_route("/api/users", "POST")


@app.post("/api/users", response_model=schemas.UserOut)
def create_user_v2(payload: _UserCreate2,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.STAFF_EDIT))):
    digits = _re.sub(r"\D", "", payload.phone or "")
    if len(digits) < 7:
        raise HTTPException(400, "Telefon raqamni kiriting — u login "
                                 "o'rnida ishlatiladi")
    username = (payload.username or "").strip() or digits
    password = payload.password or "jonyjony"
    if payload.role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    M._guard_role_assignment(user, payload.role, payload.branch_id)
    if user.role == roles.BRANCH_MANAGER \
            and not M._in_user_branches(db, user, payload.branch_id):
        raise HTTPException(403, "Faqat o'z filialingizga xodim "
                                 "qo'sha olasiz")
    # QORA RO'YXAT (2026-09-16): xodim sifatida ochib bo'lmaydi
    if payload.role not in roles.EXTERNAL_ROLES:
        import blacklist as _bl
        _bl.guard_hire(db, payload.full_name, payload.phone)
    if db.query(models.User).filter(
            models.User.username == username).first():
        raise HTTPException(400, "Bu login band — bu raqam bilan akkaunt "
                                 "allaqachon ochilgan bo'lishi mumkin")
    # Standart "jonyjony" parolga qoida qo'llanmaydi — kirgach
    # o'zgartirish tavsiya etiladi. O'zi kiritgan parol esa tekshiriladi.
    if payload.password and not roles.password_ok(password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)
    _bids = payload.branch_ids or []
    _primary = payload.branch_id or (_bids[0] if _bids else None)
    new_user = models.User(
        username=username,
        password_hash=_hash_pw(password),
        full_name=payload.full_name,
        role=payload.role,
        branch_id=_primary,
        fix_salary=payload.fix_salary,
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
    if _bids:
        M._sync_user_branches(db, new_user, _bids)
    M._smm_new_staff_task(db, new_user)
    M._ensure_teacher_card(db, new_user)
    db.commit()
    # DIQQAT: bu funksiya auth_users.py:create_user()'ni TO'LIQ
    # ALMASHTIRADI (_drop_route yuqorida) - o'sha yerdagi audit.log
    # chaqiruvi bu yo'lda HECH QACHON ishga tushmaydi. Shuning uchun
    # audit yozuvi shu yerda, HAQIQIY ishlaydigan versiyada ham
    # takrorlanadi.
    audit.log(db, user, entity="user", action="create",
              entity_id=new_user.id, entity_label=new_user.full_name,
              note=f"Rol: {roles.UZ_LABELS.get(new_user.role, new_user.role)}",
              commit=True)
    return new_user

# =====================================================================
#  XONALAR FILIALGA QAT'IY BOG'LANADI
#  Har filialning o'z xonalari; ro'yxat filial almashtirgichga bo'ysunadi;
#  yangi xona filialsiz ochilmaydi (filial sig'imi xonalardan chiqadi).
# =====================================================================
_drop_route("/api/rooms", "GET")


@app.get("/api/rooms")
def list_rooms_v2(branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_STAFF))):
    q = scope_to_branch(db.query(models.Room), models.Room, user, branch_id)
    rooms = q.order_by(models.Room.name).all()
    by_room = {}
    for g in (db.query(models.Group)
              .filter(models.Group.room_id.isnot(None)).all()):
        by_room.setdefault(g.room_id, []).append(g)
    return [M._room_out(r, by_room.get(r.id, [])) for r in rooms]


_drop_route("/api/rooms", "POST")


@app.post("/api/rooms")
def create_room_v2(payload: schemas.RoomCreate,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ACADEMIC_ACCESS))):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    if not data.get("branch_id"):
        raise HTTPException(400, "Xonaning filialini tanlang \u2014 har bir "
                                 "filialning o'z xonalari bo'ladi")
    r = models.Room(**data)
    db.add(r)
    db.commit()
    db.refresh(r)
    audit.log(db, user, entity="room", action="create", entity_id=r.id,
              entity_label=r.name, new_value=r.capacity,
              branch_id=r.branch_id, commit=True)
    return M._room_out(r)

# =====================================================================
#  USTOZ GURUH CHEGARASI: FAQAT ASOSCHI "BARIBIR OCHISH" QILA OLADI
#  Junior 1 ta, Middle 2-3 ta... — chegaradan oshsa: asoschiga
#  ogohlantirish + "baribir saqlash" tugmasi; boshqalarga QAT'IY taqiq.
# =====================================================================
def _find_endpoint(path: str, method: str):
    """Berilgan yo'l+metodga mos endpoint funksiyasini topadi - pastda
    ko'plab joyda "_orig_xxx = _find_endpoint(...)" qilib asl
    funksiyani ushlab, keyin uni o'z ichida chaqiradigan "_v2" wrapper
    yozish uchun ishlatiladi.

    2026-08: main.py bo'lindi - _drop_route()dagi bilan bir xil sabab
    bilan (routerlar endi _IncludedRouter ichida joylashadi) bu yerda
    ham ichkariga qarab qidirish kerak, aks holda _orig_xxx doim None
    bo'lib, pastdagi "if _orig_xxx is not None:" bloklari sukut bilan
    ishlamay qolar edi (asl route ustidan yozilmasdan, eskisi xizmat
    qilishda davom etardi)."""
    def _matches(r):
        return getattr(r, "path", None) == path and \
            method in (getattr(r, "methods", None) or [])

    for r in app.router.routes:
        if _matches(r):
            return r.endpoint
        ic = getattr(r, "include_context", None)
        nested = getattr(ic, "included_router", None) if ic else None
        if nested is not None:
            for nr in nested.routes:
                if _matches(nr):
                    return nr.endpoint
    return None


_orig_create_group = _find_endpoint("/api/groups", "POST")
_orig_update_group = _find_endpoint("/api/groups/{group_id}", "PUT")

# Asl tekshiruvda chegara "block" (hech kim o'tolmaydi) edi. Endi u
# "warn"ga tushiriladi — roles.GROUP_LIMIT_OVERRIDE dagi rollar 409
# ogohlantirish olib "baribir saqlash" qila oladi. Qolganlarni esa
# pastdagi guard har qanday holatda 400 bilan to'xtatadi. Qayta
# tayyorlash (remediation) taqig'i esa "chegara" so'zisiz — u
# block'ligicha qoladi.
#
# 2026-08-10: ro'yxatga HR MENEJER ham qo'shildi (Jahongir so'radi) —
# ilgari faqat asoschi o'tardi va HR guruhni umuman saqlay olmasdi.
_orig_check_teacher_load = M._check_teacher_load


def _check_teacher_load_soft(db, teacher_id, group_id):
    problems = _orig_check_teacher_load(db, teacher_id, group_id)
    for p in problems:
        if p.get("key") == "teacher_overload" and "chegara" in p.get("message", ""):
            p["severity"] = "warn"
    return problems


M._check_teacher_load = _check_teacher_load_soft


def _own_partner_branch(db: Session, user, branch_id) -> bool:
    """Xodimning ASOSIY ish joyi hamkor markaz (Stetch) va guruh ham
    shu markazniki (2026-10-03, Jahongir: Stetch egasi Husayn uchun
    "baribir ochilsin"). Lavozimidan qat'i nazar — hamkor markazni
    o'zi boshqaradi; boshqa filialga bu ruxsat o'tmaydi."""
    if not user.branch_id:
        return False
    b = db.query(models.Branch).get(user.branch_id)
    if not b or not getattr(b, "is_partner", 0):
        return False
    return not branch_id or int(branch_id) == user.branch_id


def _teacher_limit_guard(db: Session, teacher_id, group_id, user,
                         branch_id=None):
    """Chegaradan oshganda RUXSATI YO'Q rollarga qattiq taqiq.

    Ruxsati borlar (roles.GROUP_LIMIT_OVERRIDE — asoschi va HR
    menejer; o'z hamkor markazida — uning xodimi) bu yerdan o'tib
    ketadi va yuqoridagi "warn" tufayli 409 ogohlantirish oladi:
    "baribir saqlash" mumkin."""
    if not teacher_id or _has_role(user, roles.GROUP_LIMIT_OVERRIDE):
        return
    if group_id and not branch_id:
        g = db.query(models.Group).get(group_id)
        branch_id = g.branch_id if g else None
    if _own_partner_branch(db, user, branch_id):
        return
    problems = [p for p in _orig_check_teacher_load(db, teacher_id, group_id)
                if p.get("key") == "teacher_overload"]
    if problems:
        for p in problems:
            p["severity"] = "block"
        raise HTTPException(400, {
            "message": "Mumkin emas: " + problems[0]["message"],
            "problems": problems,
        })


if _orig_create_group is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v2(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE, roles.ADMINISTRATOR, roles.SALES_MANAGER))):
        _teacher_limit_guard(db, payload.teacher_id, None, user,
                             payload.branch_id or user.branch_id)
        return _orig_create_group(payload=payload, force=force,
                                  db=db, user=user)


if _orig_update_group is not None:
    _drop_route("/api/groups/{group_id}", "PUT")

    @app.put("/api/groups/{group_id}")
    def update_group_v2(group_id: int, payload: schemas.GroupUpdate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        fields = payload.model_dump(exclude_unset=True)
        if "teacher_id" in fields and fields.get("teacher_id"):
            _teacher_limit_guard(db, fields["teacher_id"], group_id, user)
        return _orig_update_group(group_id=group_id, payload=payload,
                                  force=force, db=db, user=user)

# =====================================================================
#  ASOSCHI DASHBOARDI FILIAL ALMASHTIRGICHGA BO'YSUNADI
#  Tepada filial tanlansa — kartalar va tushum grafigi o'sha filial
#  bo'yicha; "Barcha filiallar"da — umumiy. (Avval doim umumiy edi.)
# =====================================================================
from datetime import timedelta as _td

import billing as _billing


_drop_route("/api/dashboard", "GET")


@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def dashboard_v2(branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(M.get_current_user)):
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
    active = student_q.filter(models.Student.status == "active").count()
    trial = student_q.filter(models.Student.status == "trial").count()
    frozen = student_q.filter(models.Student.status == "frozen").count()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).count()
    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher,
                               user, branch_id).count()

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
        firsts = M._payment_first_dates(db)
        month_new_count = sum(
            1 for p in pays if firsts.get(p.student_id) == p.created_at
        )

    # O'quvchi/ota-ona hisoblari xodim emas (2026-09-26)
    staff_count = scope_to_branch(
        db.query(models.User), models.User, user, branch_id
    ).filter(models.User.is_active == 1,
             models.User.role.notin_(tuple(roles.EXTERNAL_ROLES))).count()

    # 2026-08-15: ilgari HAR O'QUVCHIGA alohida balans so'rovi ketardi —
    # 700 o'quvchi = 700 so'rov, Dashboard shu sababdan sekin edi.
    # _balances_bulk hammasini bitta so'rovda yig'adi; natija AYNAN
    # o'sha (ikkalasi ham payments.amount yig'indisi).
    from common import _balances_bulk as _bb
    _bal = _bb(db, [s.id for s in all_students])
    total_debt = sum(b for b in _bal.values() if b < 0)
    debtor_count = sum(1 for b in _bal.values() if b < 0)

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


_drop_route("/api/dashboard/trend", "GET")


@app.get("/api/dashboard/trend")
def dashboard_trend_v2(months: int = 6,
                       branch_id: int | None = None,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(M.get_current_user)):
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
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
        start, end = _billing.month_bounds(yy, mm)
        income = 0.0
        if student_ids:
            income = (
                db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.kind == "payment")
                .filter(models.Payment.created_at >= start)
                .filter(models.Payment.created_at < end + _td(days=1))
                .filter(models.Payment.student_id.in_(student_ids))
                .scalar()
                or 0.0
            )
        results.append({"period": f"{yy:04d}-{mm:02d}",
                        "income": float(income)})
    return results

# =====================================================================
#  DARS KO'CHIRILDI / O'RINBOSAR — ADMIN VA O'QUV BO'LIMIGA XABAR,
#  JADVALDA KO'RINISH
#  Admin jadvalga qarab yangi o'quvchini noto'g'ri kunga chaqirib
#  qo'ymasligi uchun: (1) har bir tasdiqlangan ko'chirish/o'rinbosarlik
#  administrator va o'quv bo'limi rahbariga vazifa-xabar bo'lib boradi;
#  (2) Dars jadvali sahifasida yaqin kunlardagi o'zgarishlar chiqadi.
# =====================================================================
def _lesson_change_task(db: Session, g, title: str, body: str) -> None:
    """Guruh filialidagi administratorlar va o'quv bo'limi rahbarlariga
    (filialga bog'lanmaganlariga ham) alohida-alohida vazifa-xabar."""
    users = (db.query(models.User)
             .filter(models.User.is_active == 1,
                     models.User.role.in_((roles.ADMINISTRATOR,
                                           roles.ACADEMIC_HEAD)))
             .all())
    for u in users:
        if u.branch_id and g.branch_id and u.branch_id != g.branch_id:
            continue
        t = models.Task(
            title=title, description=body, assignee_id=u.id,
            branch_id=g.branch_id,
            deadline=date.today() + _td(days=2),
            priority="normal", source="manual", created_by="Tizim")
        db.add(t)
        db.flush()
        M._ensure_public_id(db, "task", t)
    db.commit()


_orig_my_resched_add = _find_endpoint("/api/me/reschedules", "POST")
_orig_resched_decide = _find_endpoint("/api/reschedules/{rid}/decide", "POST")
_orig_sub_decide = _find_endpoint("/api/me/substitutions/{sid}/decide", "POST")


if _orig_my_resched_add is not None:
    _drop_route("/api/me/reschedules", "POST")

    @app.post("/api/me/reschedules")
    def my_reschedule_add_v2(payload: schemas.RescheduleIn,
                             db: Session = Depends(get_db),
                             user=Depends(require_role(*roles.SELF_STATS))):
        out = _orig_my_resched_add(payload=payload, db=db, user=user)
        try:
            if out.get("status") == "auto":
                g = db.query(models.Group).get(payload.group_id)
                if g is not None:
                    _lesson_change_task(
                        db, g,
                        title=(f"Dars ko'chirildi: {g.name} "
                               f"{payload.from_date} \u2192 {payload.to_date}"),
                        body=(f"{user.full_name} \"{g.name}\" guruhining "
                              f"{payload.from_date} dagi darsini "
                              f"{payload.to_date} ga ko'chirdi. "
                              f"Sabab: {out.get('reason_label') or payload.reason or '-'}. "
                              f"Yangi o'quvchini jadvalga qarab chaqirishda "
                              f"shuni hisobga oling."))
        except Exception:
            pass
        return out


# GET /api/reschedules (rahbariyat ro'yxati) - ilgari umuman
# almashtirilmagan edi, shuning uchun yuqoridagi (fayl boshidagi)
# tuzatish bo'lmasa ham, bo'lsa ham HR menejerga yetib bormas edi -
# main.py to'liq yuklanib bo'lgach (shu jumladan groups_lessons.py'ning
# @router.get("/api/reschedules") qatori) entry.py o'zining BIRINCHI
# qatoridayoq (`from main import ...`) shuni chaqiradi, ya'ni entry.py
# tanasi hali bitta ham qator ishlamasidan turib bu qaror allaqachon
# qabul qilingan bo'lardi.
_cur_reschedules_list = _find_endpoint("/api/reschedules", "GET")

if _cur_reschedules_list is not None:
    _drop_route("/api/reschedules", "GET")

    @app.get("/api/reschedules")
    def reschedules_list_v2(status: str | None = None,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.RESCHEDULE_APPROVE))):
        return _cur_reschedules_list(status=status, db=db, user=user)


if _orig_resched_decide is not None:
    _drop_route("/api/reschedules/{rid}/decide", "POST")

    @app.post("/api/reschedules/{rid}/decide")
    def reschedule_decide_v2(rid: int, payload: schemas.RescheduleDecision,
                             db: Session = Depends(get_db),
                             user=Depends(require_role(
                                 *roles.RESCHEDULE_APPROVE))):
        out = _orig_resched_decide(rid=rid, payload=payload, db=db, user=user)
        try:
            if payload.decision == "approved":
                r = db.query(models.LessonReschedule).get(rid)
                g = db.query(models.Group).get(r.group_id) if r else None
                if g is not None:
                    _lesson_change_task(
                        db, g,
                        title=(f"Dars ko'chirildi: {g.name} "
                               f"{r.from_date} \u2192 {r.to_date}"),
                        body=(f"\"{g.name}\" guruhining {r.from_date} dagi "
                              f"darsi {r.to_date} ga ko'chirildi "
                              f"(tasdiqladi: {user.full_name}). "
                              f"Yangi o'quvchini jadvalga qarab chaqirishda "
                              f"shuni hisobga oling."))
        except Exception:
            pass
        return out


if _orig_sub_decide is not None:
    _drop_route("/api/me/substitutions/{sid}/decide", "POST")

    @app.post("/api/me/substitutions/{sid}/decide")
    def my_substitution_decide_v2(sid: int,
                                  payload: schemas.SubstitutionDecision,
                                  db: Session = Depends(get_db),
                                  user=Depends(require_role(
                                      *roles.SELF_STATS))):
        out = _orig_sub_decide(sid=sid, payload=payload, db=db, user=user)
        try:
            if payload.decision == "accepted":
                s = db.query(models.Substitution).get(sid)
                g = db.query(models.Group).get(s.group_id) if s else None
                if g is not None:
                    orig_t = (db.query(models.Teacher)
                              .get(s.original_teacher_id)
                              if s.original_teacher_id else None)
                    _lesson_change_task(
                        db, g,
                        title=(f"O'rinbosar dars o'tadi: {g.name} "
                               f"({s.lesson_date})"),
                        body=(f"\"{g.name}\" guruhining {s.lesson_date} dagi "
                              f"darsini {orig_t.full_name if orig_t else '-'} "
                              f"o'rniga {user.full_name} o'tadi."))
        except Exception:
            pass
        return out


_orig_timetable = _find_endpoint("/api/timetable", "GET")

if _orig_timetable is not None:
    _drop_route("/api/timetable", "GET")

    @app.get("/api/timetable")
    def timetable_v2(branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.TEACHING_STAFF,
                                               roles.HR_MANAGER))):
        out = _orig_timetable(branch_id=branch_id, db=db, user=user)
        try:
            gids = {it["group_id"] for it in out.get("items", [])}
            today = date.today()
            horizon = today + _td(days=30)
            changes = []
            if gids:
                gmap = {g.id: g for g in db.query(models.Group)
                        .filter(models.Group.id.in_(gids)).all()}
                rs = (db.query(models.LessonReschedule)
                      .filter(models.LessonReschedule.group_id.in_(gids),
                              models.LessonReschedule.status.in_(
                                  ("auto", "approved")),
                              models.LessonReschedule.to_date >= today,
                              models.LessonReschedule.from_date <= horizon)
                      .all())
                for r in rs:
                    g = gmap.get(r.group_id)
                    t = (db.query(models.Teacher).get(r.teacher_id)
                         if r.teacher_id else None)
                    changes.append({
                        "kind": "move", "group_id": r.group_id,
                        "group": g.name if g else "",
                        "teacher": t.full_name if t else None,
                        "from_date": r.from_date.isoformat(),
                        "to_date": r.to_date.isoformat(),
                        "sort": r.from_date.isoformat(),
                    })
                ss = (db.query(models.Substitution)
                      .filter(models.Substitution.group_id.in_(gids),
                              models.Substitution.status == "accepted",
                              models.Substitution.lesson_date >= today,
                              models.Substitution.lesson_date <= horizon)
                      .all())
                for s in ss:
                    g = gmap.get(s.group_id)
                    ot = (db.query(models.Teacher)
                          .get(s.original_teacher_id)
                          if s.original_teacher_id else None)
                    st = (db.query(models.Teacher)
                          .get(s.substitute_teacher_id)
                          if s.substitute_teacher_id else None)
                    changes.append({
                        "kind": "sub", "group_id": s.group_id,
                        "group": g.name if g else "",
                        "teacher": ot.full_name if ot else None,
                        "substitute": st.full_name if st else None,
                        "date": s.lesson_date.isoformat(),
                        "sort": s.lesson_date.isoformat(),
                    })
            changes.sort(key=lambda x: x["sort"])
            out["changes"] = changes
        except Exception:
            out.setdefault("changes", [])
        return out

# --- Jadval GRID ko'rinishida ham o'zgarishlar banneri ---
_orig_timetable_grid = _find_endpoint("/api/timetable/grid", "GET")

if _orig_timetable_grid is not None:
    _drop_route("/api/timetable/grid", "GET")

    @app.get("/api/timetable/grid")
    def timetable_grid_v2(day: str = "mon",
                          branch_id: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(M.require_perm("timetable", "view"))):
        out = _orig_timetable_grid(day=day, branch_id=branch_id,
                                   db=db, user=user)
        try:
            gq = scope_to_branch(db.query(models.Group), models.Group,
                                 user, branch_id)
            gmap = {g.id: g for g in gq.all()}
            gids = set(gmap)
            today = date.today()
            horizon = today + _td(days=30)
            changes = []
            if gids:
                rs = (db.query(models.LessonReschedule)
                      .filter(models.LessonReschedule.group_id.in_(gids),
                              models.LessonReschedule.status.in_(
                                  ("auto", "approved")),
                              models.LessonReschedule.to_date >= today,
                              models.LessonReschedule.from_date <= horizon)
                      .all())
                for r in rs:
                    g = gmap.get(r.group_id)
                    t = (db.query(models.Teacher).get(r.teacher_id)
                         if r.teacher_id else None)
                    changes.append({
                        "kind": "move", "group_id": r.group_id,
                        "group": g.name if g else "",
                        "teacher": t.full_name if t else None,
                        "from_date": r.from_date.isoformat(),
                        "to_date": r.to_date.isoformat(),
                        "sort": r.from_date.isoformat(),
                    })
                ss = (db.query(models.Substitution)
                      .filter(models.Substitution.group_id.in_(gids),
                              models.Substitution.status == "accepted",
                              models.Substitution.lesson_date >= today,
                              models.Substitution.lesson_date <= horizon)
                      .all())
                for s in ss:
                    g = gmap.get(s.group_id)
                    ot = (db.query(models.Teacher)
                          .get(s.original_teacher_id)
                          if s.original_teacher_id else None)
                    st = (db.query(models.Teacher)
                          .get(s.substitute_teacher_id)
                          if s.substitute_teacher_id else None)
                    changes.append({
                        "kind": "sub", "group_id": s.group_id,
                        "group": g.name if g else "",
                        "teacher": ot.full_name if ot else None,
                        "substitute": st.full_name if st else None,
                        "date": s.lesson_date.isoformat(),
                        "sort": s.lesson_date.isoformat(),
                    })
            changes.sort(key=lambda x: x["sort"])
            out["changes"] = changes
        except Exception:
            out.setdefault("changes", [])
        return out


# =====================================================================
#  OMBOR (kitoblar, qabul qilish, hisobot) + LID MAS'ULI + JAMOAVIY KPI
# =====================================================================
from datetime import datetime as _dt2

from database import SessionLocal as _SessionLocal

# "Admin" deb ikkala rol tushuniladi: sotuv menejeri (Administrator) va
# administrator (qabul). Lidga mas'ul faqat shulardan bo'ladi.
_ADMIN_ROLES = (roles.ADMINISTRATOR, roles.SALES_MANAGER)
_BOOK_KINDS = ("book", "welcome_pack")

# --- stock_moves: "qabul qilib oldim" ustunlari (idempotent ALTER) ---
try:
    _sm_cols = {c["name"]
                for c in _sa_inspect(_engine).get_columns("stock_moves")}
    with _engine.begin() as _con:
        if "accepted_by" not in _sm_cols:
            _con.execute(_sa_text(
                "ALTER TABLE stock_moves ADD COLUMN accepted_by INTEGER"))
        if "accepted_at" not in _sm_cols:
            _con.execute(_sa_text(
                "ALTER TABLE stock_moves ADD COLUMN accepted_at TIMESTAMP"))
except Exception:
    pass


# --- Har filialda standart kitoblar bo'lsin ---
def _seed_books() -> None:
    db = _SessionLocal()
    try:
        defaults = [("Step 1", "book"), ("Step 2", "book"),
                    ("Step 3", "book"), ("Welcome Pack", "welcome_pack"),
                    ("IELTS Introduction", "book"),
                    ("IELTS Foundation", "book"),
                    ("Family and Friends 0", "book"),
                    ("Family and Friends 1", "book"),
                    ("Family and Friends 2", "book"),
                    ("Family and Friends 3", "book"),
                    ("Round-up 0", "book"),
                    ("Round-up 1", "book"),
                    ("Round-up 2", "book"),
                    ("Round-up 3", "book"),
                    ("Round-up 4", "book")]
        added = False
        for b in db.query(models.Branch).all():
            for name, kind in defaults:
                exists = (db.query(models.Consumable)
                          .filter(models.Consumable.branch_id == b.id,
                                  func.lower(models.Consumable.name)
                                  == name.lower())
                          .first())
                if not exists:
                    db.add(models.Consumable(
                        name=name, kind=kind, branch_id=b.id,
                        qty=0, min_qty=0, unit="dona"))
                    added = True
        if added:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


try:
    _seed_books()
except Exception:
    pass


# --- Lidga mas'ul bo'la oladiganlar: faqat adminlar ---
_orig_assignable = _find_endpoint("/api/users/assignable", "GET")

if _orig_assignable is not None:
    _drop_route("/api/users/assignable", "GET")

    @app.get("/api/users/assignable",
             response_model=list[schemas.StaffOption])
    def assignable_v2(db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.LEAD_ACCESS))):
        """Ustoz va examiner mas'ul bo'lmaydi — faqat adminlar."""
        q = scope_to_branch(db.query(models.User), models.User, user)
        return (q.filter(models.User.is_active == 1,
                         models.User.role.in_(_ADMIN_ROLES))
                .order_by(models.User.full_name).all())


# --- Lid yaratish: admin kiritsa mas'ul avtomat o'zi ---
_orig_create_lead2 = _find_endpoint("/api/leads", "POST")

if _orig_create_lead2 is not None:
    _drop_route("/api/leads", "POST")

    @app.post("/api/leads", response_model=schemas.LeadOut)
    def create_lead_v2(payload: schemas.LeadCreate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        if user.role in _ADMIN_ROLES:
            payload.assigned_user_id = user.id
        elif payload.assigned_user_id:
            a = db.query(models.User).get(payload.assigned_user_id)
            if not a or a.role not in _ADMIN_ROLES:
                raise HTTPException(
                    400, "Mas'ul xodim faqat administrator bo'la oladi")
        return _orig_create_lead2(payload=payload, db=db, user=user)


# --- Lid tahrirlash: mas'ulsiz lidni admin surse — o'zi mas'ul bo'ladi ---
_orig_update_lead2 = _find_endpoint("/api/leads/{lead_id}", "PUT")

if _orig_update_lead2 is not None:
    _drop_route("/api/leads/{lead_id}", "PUT")

    @app.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
    def update_lead_v2(lead_id: int, payload: schemas.LeadUpdate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        want = getattr(payload, "assigned_user_id", None)
        if want:
            a = db.query(models.User).get(want)
            if not a or a.role not in _ADMIN_ROLES:
                raise HTTPException(
                    400, "Mas'ul xodim faqat administrator bo'la oladi")
        out = _orig_update_lead2(lead_id=lead_id, payload=payload,
                                 db=db, user=user)
        try:
            lead = db.query(models.Lead).get(lead_id)
            if (lead is not None and not lead.assigned_user_id
                    and user.role in _ADMIN_ROLES):
                lead.assigned_user_id = user.id
                db.commit()
                db.refresh(lead)
                out = lead
        except Exception:
            pass
        return out


# --- Marketing (inbox) lidi: filialda bitta admin bo'lsa — avtomat u ---
_orig_msg_lead = _find_endpoint("/api/inbox/{mid}/lead", "POST")

if _orig_msg_lead is not None:
    _drop_route("/api/inbox/{mid}/lead", "POST")

    @app.post("/api/inbox/{mid}/lead")
    def message_to_lead_v2(mid: int, payload: schemas.MessageToLead,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.INBOX_ACCESS))):
        out = _orig_msg_lead(mid=mid, payload=payload, db=db, user=user)
        try:
            lid = out.get("lead_id") if isinstance(out, dict) else None
            lead = db.query(models.Lead).get(lid) if lid else None
            if lead is not None and not lead.assigned_user_id and lead.branch_id:
                admins = (db.query(models.User)
                          .filter(models.User.is_active == 1,
                                  models.User.role.in_(_ADMIN_ROLES),
                                  models.User.branch_id == lead.branch_id)
                          .all())
                if len(admins) == 1:
                    lead.assigned_user_id = admins[0].id
                    db.commit()
        except Exception:
            pass
        return out


# --- Kitoblar ro'yxati (to'lov oynasi uchun) ---
_INV_BOOK_ROLES = tuple(dict.fromkeys(
    list(roles.INVENTORY_VIEW) + list(_ADMIN_ROLES)))


@app.get("/api/consumables/books")
def list_books_v2(branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*_INV_BOOK_ROLES))):
    q = scope_to_branch(db.query(models.Consumable), models.Consumable,
                        user, branch_id)
    rows = (q.filter(models.Consumable.kind.in_(_BOOK_KINDS))
            .order_by(models.Consumable.name).all())
    if not rows:
        # Yangi filial — standart kitoblarni shu yerda ham yaratib olamiz
        _seed_books()
        rows = (q.filter(models.Consumable.kind.in_(_BOOK_KINDS))
                .order_by(models.Consumable.name).all())
    return [{"id": c.id, "name": c.name, "qty": c.qty or 0,
             "unit": c.unit or "dona", "branch_id": c.branch_id}
            for c in rows]


# --- Kitob berish (yangi to'lov bilan): ombordan kamayadi ---
class _GiveBookIn(_BM):
    student_id: int | None = None
    note: str | None = None


@app.post("/api/consumables/{cid}/give-book")
def give_book_v2(cid: int, payload: _GiveBookIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_INV_BOOK_ROLES))):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    if (c.qty or 0) < 1:
        raise HTTPException(
            409, f"Omborda yo'q: \"{c.name}\" qoldig'i 0. "
                 "Filial rahbariga ayting — kirim qilinsin.")
    st = (db.query(models.Student).get(payload.student_id)
          if payload.student_id else None)
    note = "Kitob berildi (to'lov bilan)"
    if st:
        note += f": {st.full_name}"
    if payload.note:
        note += f" — {payload.note}"
    db.add(models.StockMove(consumable_id=c.id, delta=-1, reason="out",
                            note=note, created_by=user.full_name))
    c.qty = (c.qty or 0) - 1
    db.commit()
    try:
        M._check_stock(db, c)
        db.commit()
    except Exception:
        pass
    return {"ok": True, "qty": c.qty, "name": c.name}


# --- Qabul qilinmagan kirimlar ---
@app.get("/api/stock-moves/pending")
def pending_stock_moves_v2(branch_id: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*_INV_BOOK_ROLES))):
    rows = db.execute(_sa_text(
        "SELECT sm.id, sm.delta, sm.note, sm.created_by, sm.created_at, "
        "c.name, c.unit, c.branch_id "
        "FROM stock_moves sm JOIN consumables c ON c.id = sm.consumable_id "
        "WHERE sm.reason = 'in' AND sm.accepted_at IS NULL "
        "ORDER BY sm.created_at DESC")).fetchall()
    if user.role in tuple(roles.ORG_WIDE_ROLES):
        bid = branch_id
    else:
        bid = user.branch_id
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    out = []
    for r in rows:
        if bid and r[7] and r[7] != bid:
            continue
        out.append({
            "id": r[0], "qty": abs(r[1] or 0), "note": r[2], "by": r[3],
            "created_at": (r[4].isoformat()
                           if hasattr(r[4], "isoformat") else str(r[4] or "")),
            "name": r[5], "unit": r[6] or "dona",
            "branch": bnames.get(r[7], "—"),
        })
    return {"rows": out,
            "can_accept": user.role in
            ((roles.FOUNDER, roles.BRANCH_MANAGER) + _ADMIN_ROLES)}


# --- Kirimni qabul qilish: filial rahbari, bo'lmasa admin ---
@app.post("/api/stock-moves/{mid}/accept")
def accept_stock_move_v2(mid: int, db: Session = Depends(get_db),
                         user=Depends(require_role(
                             roles.FOUNDER, roles.BRANCH_MANAGER,
                             *_ADMIN_ROLES))):
    row = db.execute(_sa_text(
        "SELECT sm.id, sm.reason, sm.accepted_at, c.branch_id, c.name "
        "FROM stock_moves sm JOIN consumables c ON c.id = sm.consumable_id "
        "WHERE sm.id = :i"), {"i": mid}).fetchone()
    if not row:
        raise HTTPException(404, "Harakat topilmadi")
    if row[1] != "in":
        raise HTTPException(400, "Faqat kirim qabul qilinadi")
    if row[2] is not None:
        raise HTTPException(400, "Bu kirim allaqachon qabul qilingan")
    bid = row[3]
    if (user.role != roles.FOUNDER and user.branch_id and bid
            and user.branch_id != bid):
        raise HTTPException(403, "Bu boshqa filialning ombori")
    if user.role in _ADMIN_ROLES:
        bm = (db.query(models.User)
              .filter(models.User.role == roles.BRANCH_MANAGER,
                      models.User.is_active == 1,
                      models.User.branch_id == bid)
              .first())
        if bm:
            raise HTTPException(
                403, f"Qabul qilishni filial rahbari ({bm.full_name}) "
                     "belgilashi kerak")
    db.execute(_sa_text(
        "UPDATE stock_moves SET accepted_by = :u, accepted_at = :t "
        "WHERE id = :i"),
        {"u": user.id, "t": _dt2.utcnow(), "i": mid})
    db.commit()
    return {"ok": True}


# --- Kitob hisoboti: qaysi filialda nechta qoldi ---
_BOOK_REPORT_ALL = (roles.FOUNDER, roles.FINANCE_DIRECTOR,
                    roles.FACILITY_MANAGER, roles.HR_MANAGER)


@app.get("/api/inventory/book-report")
def book_report_v2(db: Session = Depends(get_db),
                   user=Depends(require_role(
                       *(_BOOK_REPORT_ALL + (roles.BRANCH_MANAGER,))))):
    q = db.query(models.Consumable).filter(
        models.Consumable.kind.in_(_BOOK_KINDS))
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(M._branch_in(db, user, models.Consumable.branch_id))
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = q.all()
    names = sorted({c.name for c in rows})
    per: dict = {}
    for c in rows:
        b = bnames.get(c.branch_id, "Filialsiz")
        per.setdefault(b, {})
        per[b][c.name] = (per[b].get(c.name, 0) or 0) + (c.qty or 0)
    return {
        "books": names,
        "rows": [{"branch": b,
                  "counts": {n: v.get(n, 0) for n in names},
                  "total": sum(v.values())}
                 for b, v in sorted(per.items())],
    }


# --- Adminlar KPI: eski to'lov yig'ish JAMOAVIY (filial bo'yicha) ---
_drop_route("/api/kpi/admins", "GET")


@app.get("/api/kpi/admins", response_model=schemas.AdminKpiResult)
def admin_kpi_v2(year: int, month: int, branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.KPI_VIEW))):
    """Adminlar KPI. Farqi bittagina: ro'yxatga "Administrator (qabul)"
    roli ham kiradi. Hisobning O'ZI dashboard.compute_admin_kpi da.

    2026-08-30 — BU YERDA NUSXA TURGAN EDI. Hisob ikki joyda
    takrorlangani uchun dashboard.py tuzatilganda jonli saytda
    baribir ESKI mantiq ishlab turdi (yangi mijoz filial bo'yicha
    yig'ilardi). Endi nusxa yo'q: bitta manba, ikkala yo'l ham
    shuni chaqiradi.

    ESKI TO'LOV yig'ish bonusi — JAMOAVIY (filial bo'yicha): bir
    filialda ikkita admin bo'lsa, ikkalasiga ham to'liq bonus.
    YANGI MIJOZ bonusi — SHAXSIY (Jahongir, 2026-08-30: "kim yangi
    to'lov qildirsa o'ziga hisoblanishi kerak")."""
    return M.compute_admin_kpi(db, user, year, month,
                               admin_roles=_ADMIN_ROLES,
                               branch_id=branch_id)


# MyProfile ham shu hisobdan foydalanadi
M.admin_kpi = admin_kpi_v2

# =====================================================================
#  RUNTIME ROL OVERRIDE — roles.py fayli katta, o'zgarishlar shu yerda
# =====================================================================
# Audit ro'yxati: moliyachi va bosh examiner chiqadi, HR kiradi.
roles.AUDIT_VIEW[:] = [roles.FOUNDER, roles.BRANCH_MANAGER,
                       roles.HR_MANAGER]
# SMM (kontent so'rovi) — o'quv bo'limi rahbariga kerak emas.
roles.CONTENT_REQUESTER[:] = [r for r in roles.CONTENT_REQUESTER
                              if r != roles.ACADEMIC_HEAD]
# Ruxsat matritsasi (runtime o'qiladi):
try:
    roles.DEFAULT_MATRIX[roles.FINANCE_DIRECTOR].pop("audit", None)
    roles.DEFAULT_MATRIX[roles.HEAD_EXAMINER].pop("audit", None)
    roles.DEFAULT_MATRIX[roles.HR_MANAGER]["audit"] = {"view", "export"}
except Exception:
    pass

# Audit endpointlari dekoratsiya paytida eski ro'yxatni "muhrlab" olgan —
# yangi ro'yxat bilan qayta ulaymiz.
_orig_audit_list = _find_endpoint("/api/audit", "GET")
_orig_audit_meta = _find_endpoint("/api/audit/meta", "GET")

if _orig_audit_list is not None:
    _drop_route("/api/audit", "GET")

    @app.get("/api/audit")
    def audit_list_v2(entity: str | None = None,
                      entity_id: int | None = None,
                      action: str | None = None,
                      user_id: int | None = None,
                      days: int = 90,
                      limit: int = 200,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(
                          roles.FOUNDER, roles.BRANCH_MANAGER,
                          roles.HR_MANAGER))):
        return _orig_audit_list(entity=entity, entity_id=entity_id,
                                action=action, user_id=user_id, days=days,
                                limit=limit, db=db, user=user)

if _orig_audit_meta is not None:
    _drop_route("/api/audit/meta", "GET")

    @app.get("/api/audit/meta")
    def audit_meta_v2(user=Depends(require_role(
            roles.FOUNDER, roles.BRANCH_MANAGER, roles.HR_MANAGER))):
        return _orig_audit_meta(user=user)

# =====================================================================
#  HR MENEJERGA QO'SHIMCHA HUQUQLAR
#  Eski yo'qlama qo'yish, guruh ochish/tahrirlash, o'quvchi qo'shish.
# =====================================================================
_HRM = roles.HR_MANAGER

# O'tgan kun yo'qlamasi — endpoint ichida runtime tekshiriladi:
roles.PAST_ATTENDANCE[:] = [roles.FOUNDER, roles.ACADEMIC_HEAD, _HRM]
# Guruh boshqaruvi ro'yxatiga ham (runtime o'qiydigan joylar uchun):
if _HRM not in roles.GROUP_MANAGE:
    roles.GROUP_MANAGE.append(_HRM)

# Ruxsat matritsasi (Ruxsatlar sahifasida ham to'g'ri ko'rinsin):
try:
    _hrm_m = roles.DEFAULT_MATRIX[roles.HR_MANAGER]
    _hrm_m["students"] = {"view", "create", "edit"}
    _hrm_m["groups"] = {"view", "create", "edit"}
    _hrm_m["attendance"] = {"view", "create", "edit"}
except Exception:
    pass


# Yo'qlama saqlash — HR ham (o'tgan kunlar uchun ham, tepadagi
# PAST_ATTENDANCE ro'yxati orqali):
_orig_save_att = _find_endpoint("/api/lessons/{lesson_id}/attendance",
                                "PUT")

if _orig_save_att is not None:
    _drop_route("/api/lessons/{lesson_id}/attendance", "PUT")

    @app.put("/api/lessons/{lesson_id}/attendance")
    def save_attendance_v2(lesson_id: int,
                           payload: schemas.AttendanceBulk,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *(tuple(roles.TEACHING_ACCESS) + (_HRM,))))):
        return _orig_save_att(lesson_id=lesson_id, payload=payload,
                              db=db, user=user)


# Dars (yo'qlama kuni) qo'shish — HR ham:
_orig_add_lesson = _find_endpoint("/api/groups/{group_id}/lessons", "POST")

if _orig_add_lesson is not None:
    _drop_route("/api/groups/{group_id}/lessons", "POST")

    @app.post("/api/groups/{group_id}/lessons",
              response_model=schemas.LessonOut)
    def add_lesson_v2(group_id: int, payload: schemas.LessonCreate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_role(
                          *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        return _orig_add_lesson(group_id=group_id, payload=payload,
                                db=db, user=user)


# Guruh ochish/tahrirlash — HR ham (junior chegara nazorati saqlanadi):
_cur_create_group = _find_endpoint("/api/groups", "POST")
_cur_update_group = _find_endpoint("/api/groups/{group_id}", "PUT")

if _cur_create_group is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v3(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE, roles.ADMINISTRATOR, roles.SALES_MANAGER))):
        return _cur_create_group(payload=payload, force=force,
                                 db=db, user=user)

if _cur_update_group is not None:
    _drop_route("/api/groups/{group_id}", "PUT")

    @app.put("/api/groups/{group_id}")
    def update_group_v3(group_id: int, payload: schemas.GroupUpdate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(
                            *(list(roles.GROUP_MANAGE)
                              + [roles.HR_MANAGER, roles.SALES_MANAGER,
                                 roles.ADMINISTRATOR,
                                 roles.FINANCE_DIRECTOR])))):
        return _cur_update_group(group_id=group_id, payload=payload,
                                 force=force, db=db, user=user)


# O'quvchi qo'shish/tahrirlash — HR ham:
_cur_create_student = _find_endpoint("/api/students", "POST")
_cur_update_student = _find_endpoint("/api/students/{student_id}", "PUT")

if _cur_create_student is not None:
    _drop_route("/api/students", "POST")

    @app.post("/api/students", response_model=schemas.StudentOut)
    def create_student_v2(payload: schemas.StudentCreate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        # FAQAT LIDDAN (2026-09-16, Jahongir: "oquvchini qoshish mumkin
        # bolmasin faqat liddan qoshish mumkin bo'lsin")
        if user.role not in tuple(roles.STUDENT_CREATE):
            raise HTTPException(
                403, "Yangi o'quvchi faqat Lidlar bo'limi orqali qo'shiladi: "
                     "lid kiriting va \"O'quvchiga aylantirish\" tugmasini "
                     "bosing.")
        return _cur_create_student(payload=payload, force=force,
                                   db=db, user=user)

if _cur_update_student is not None:
    _drop_route("/api/students/{student_id}", "PUT")

    @app.put("/api/students/{student_id}",
             response_model=schemas.StudentOut)
    def update_student_v2(student_id: int, payload: schemas.StudentUpdate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        return _cur_update_student(student_id=student_id, payload=payload,
                                   force=force, db=db, user=user)


# =====================================================================
#  LIDLAR: HAR FILIALNING O'Z HUDUD/MAKTAB RO'YXATI
#  (avval Zafar mahallalari hamma filialga chiqib turardi)
# =====================================================================
import re as _re2

_BEKOBOD1_AREAS = [
    "Metal", "11-mikrarayon", "12-mikrarayon", "13-mikrarayon", "Kirf",
    "Gidrometriya", "Xos", "Taqachi", "Navoiy",
]
_BEKOBOD2_AREAS = [
    "3-mikrarayon", "Semetchi", "Shaxmat", "Semgorodok",
]
_STRETINKO_AREAS = [
    "Stretinko", "Xos", "Navoiy", "20-brigada",
]
roles.BRANCH_AREAS["Bekobod 1"] = _BEKOBOD1_AREAS
roles.BRANCH_AREAS["Bekobod 2"] = _BEKOBOD2_AREAS
roles.BRANCH_AREAS["Stretinko"] = _STRETINKO_AREAS


def _norm_bname(s):
    return _re2.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _areas_for_branch_v2(name):
    """Aniq mos kelmasa ham (masalan "Bekobod-1" yozilsa) filialni
    taniydi — nomlar biroz farqlansa ro'yxat aralashib ketmasin."""
    if name:
        if name in roles.BRANCH_AREAS:
            return roles.BRANCH_AREAS[name]
        key = _norm_bname(name)
        for bname, lst in roles.BRANCH_AREAS.items():
            nb = _norm_bname(bname)
            if nb and (nb == key or nb in key):
                return lst
    # Filial noma'lum - hammasini birlashtirib ko'rsatamiz
    out = []
    for lst in roles.BRANCH_AREAS.values():
        for a in lst:
            if a not in out:
                out.append(a)
    return out


roles.areas_for_branch = _areas_for_branch_v2

# Maktablar: Bekobod 1 va Bekobod 2'da 1-25 + ixtisoslashgan. Boshqa
# filiallarda hozircha umumiy ro'yxat (1-60) qoladi - alohida ro'yxat
# aytilmagan.
_SCHOOLS_1_25 = [f"{i}-maktab" for i in range(1, 26)] + [
    "Ixtisoslashgan maktab"]
_BRANCH_SCHOOLS = {"Bekobod 1": _SCHOOLS_1_25, "Bekobod 2": _SCHOOLS_1_25}


def _schools_for_branch(name):
    if name:
        if name in _BRANCH_SCHOOLS:
            return _BRANCH_SCHOOLS[name]
        key = _norm_bname(name)
        for bname, lst in _BRANCH_SCHOOLS.items():
            if _norm_bname(bname) == key:
                return lst
    return roles.SCHOOLS


_orig_reference = _find_endpoint("/api/reference", "GET")

if _orig_reference is not None:
    _drop_route("/api/reference", "GET")

    @app.get("/api/reference")
    def reference_v2(branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
        bname = None
        bid = branch_id or user.branch_id
        if bid:
            b = db.query(models.Branch).get(bid)
            bname = b.name if b else None
        return {
            "areas": _areas_for_branch_v2(bname),
            "schools": _schools_for_branch(bname),
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
#  MUZLATILGAN O'QUVCHI YO'QLAMADA HECH KIMGA KO'RINMASIN
#  Yo'qlama - oylik hisoblanadigan hujjat, shuning uchun muzlatilgan
#  o'quvchi ko'rinib, xato yo'qlama qo'yib qo'yilmasin.
#
#  2026-08-09: bu tekshiruv ilgari FAQAT `role == TEACHER` bo'lsa
#  ishlagan — HR menejer, asoschi, filial rahbari va boshqa
#  rollarga muzlatilgan o'quvchi hali ham to'liq qator bo'lib,
#  yoqlama belgisi bilan chiqaverardi (Jahongir skrinshot bilan
#  ko'rsatdi: muzlatilgan o'quvchiga "03 avg" kuni belgi qo'yilgan
#  edi). Sabab (yo'qlama — ish haqi hujjati) ROLGA BOG'LIQ EMAS,
#  shuning uchun endi HAMMA uchun bir xil qo'llanadi.
# =====================================================================
# Muzlatilganlar davomat TARIXINI ko'radiganlar (Jahongir ro'yxati):
# administratorlar, o'quv bo'limi rahbari, HR, moliyachi, filial
# rahbarlari + asoschi. Administrator hisoblari sales_manager'ga
# birlashtirilgan - ikkala kalit ham kiritildi.
_FROZEN_HISTORY_VIEW = (
    roles.FOUNDER, roles.BRANCH_MANAGER, roles.ACADEMIC_HEAD,
    roles.HR_MANAGER, roles.FINANCE_DIRECTOR, roles.SALES_MANAGER,
    roles.ADMINISTRATOR)

_orig_att_grid = _find_endpoint("/api/groups/{group_id}/attendance", "GET")

if _orig_att_grid is not None:
    _drop_route("/api/groups/{group_id}/attendance", "GET")

    @app.get("/api/groups/{group_id}/attendance",
             response_model=schemas.AttendanceGrid)
    def attendance_grid_v2(group_id: int, year: int, month: int,
                           others: int = 0,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *roles.ATTENDANCE_VIEW))):
        result = _orig_att_grid(group_id=group_id, year=year, month=month,
                                db=db, user=user)
        # Ichki chaqiruv Pydantic model ham, oddiy dict ham qaytarishi
        # mumkin. 2026-09-21 da aynan shu yerda 500 chiqqan edi:
        # entry.py ikki marta bajarilib, bu funksiya o'z-o'zini
        # o'rab qolgan va ichkisi dict qaytargan. Ildiz sabab
        # yuqorida (sys.modules) tuzatildi; bu yer esa har ehtimolga
        # qarshi ikkala turni ham qabul qiladi.
        if isinstance(result, dict):
            data = dict(result)
        elif hasattr(result, "model_dump"):
            data = result.model_dump()
        else:
            data = result.dict()
        # 2026-08-11 (Jahongir): muzlatilganning ESKI davomat tarixi
        # rahbariyatga ko'rinsin - "ertaga bizga u kerak bo'ladi".
        # Ustoz va boshqalarga esa avvalgidek umuman chiqmaydi
        # (yangi yo'qlama qo'yib yubormasin). Rahbariyatda ham qator
        # faqat O'QISH uchun - frontend belgilashni bloklaydi,
        # backend ham saqlashda o'tkazib yuboradi.
        marked = {int(k.split(":")[1]) for k in
                  (data.get("marks") or {}).keys()}
        # GURUHDAN O'CHIRILGAN / ARXIVDAGI o'quvchi (2026-08-18,
        # Jahongir: "guruhdan ochirilgan talaba bu yerda turmasin,
        # bunaqa bolib"): jadvalda ODATIY qator bo'lib TURMAYDI.
        #   - o'sha oyda yo'qlamasi YO'Q bo'lsa - umuman chiqmaydi
        #     (skrinshotdagi bo'sh kataklar qatori aynan shu edi);
        #   - yo'qlamasi BOR bo'lsa - rahbariyatga faqat o'qish uchun
        #     kulrang qator (ustoz oyligi hujjati yo'qolmasin).
        # TUGMA BILAN OCHILADI (2026-08-20, Jahongir: "pastiga
        # ketganlar va muzaltilganlarni daovmatini korsatish degan
        # tugmani qoysak bosganda korinsin muzlatilganlar va
        # ketganlarniki ham"). others=0 (odatiy) - jadval faqat
        # faollardan iborat, toza. others=1 - rahbariyatga muzlatilgan
        # va ketganlarning tarixi ham qo'shiladi (faqat o'qish uchun).
        _gone_rows = []
        for x in list(data["students"]):
            if x.get("status") in ("archived", "left"):
                data["students"].remove(x)
                if x["id"] in marked and user.role in _FROZEN_HISTORY_VIEW:
                    x["status"] = "transferred"
                    x["note"] = ("Guruhdan o'chirilgan (arxiv) - "
                                 "yo'qlama tarixi o'qish uchun")
                    _gone_rows.append(x)
        show_others = bool(others) and user.role in _FROZEN_HISTORY_VIEW
        frozen = [x for x in data["students"]
                  if x.get("status") == "frozen"]
        act = [x for x in data["students"]
               if x.get("status") != "frozen"]
        if show_others:
            # Muzlatilganlar - tarixi bo'sh bo'lsa ham ko'rinadi
            # (holatini bilish uchun), ketganlar - yozuvi borlari.
            data["students"] = act + frozen + _gone_rows
            # BOSHQA GURUHGA O'TGANLAR (Jahongir, 2026-08-11):
            # yo'qlamasi shu guruh tarixida bor, lekin o'zi endi
            # boshqa guruhda. Satr faqat o'qish uchun ko'rinadi -
            # eski ustozning oyligi shu yozuvlardan chiqadi.
            have = {x["id"] for x in data["students"]}
            gone = marked - have
            if gone:
                for st in db.query(models.Student).filter(
                        models.Student.id.in_(gone)).all():
                    gname = st.group.name if st.group else None
                    data["students"].append({
                        "id": st.id, "full_name": st.full_name,
                        "status": "transferred",
                        "note": ("Boshqa guruhga o'tgan"
                                 + (f": {gname}" if gname else "")
                                 + " - yo'qlamalari avvalgi ustoz "
                                   "oyligida qoladi"),
                    })
        else:
            data["students"] = act

        # =============================================================
        #  KETGANNING DUMINI JADVALDAN HAM OLIB TASHLASH (2026-08-29)
        # =============================================================
        #  Jahongir: "chiqib ketgan kunida oxirida ... oxirgi 2ta dars
        #  kelmagan va chiqib ketgan, shu kelmagan darsini ayirib
        #  tashlash kerak, YO'QLAMASI YO'QOLISHI KERAK, chunki u chiqib
        #  ketgan, ustozga oylik yozilishi kerak emas"
        #
        #  Pul tomoni billing.py da kesilgan. Ekranda ham ko'rinmasin —
        #  aks holda "hisobda yo'q, lekin jadvalda qizil ✗ turibdi"
        #  degan chalkashlik qoladi va odam qайси biriga ishonishni
        #  bilmaydi.
        #
        #  Yozuv O'CHIRILMAYDI: bazada joyida qoladi, faqat shu
        #  jadvalda ko'rsatilmaydi.
        try:
            import billing as _bl
            ids = [x["id"] for x in data["students"]]
            cut = _bl.attendance_cutoff(db, ids, group_id)
            if cut:
                les = {l["id"]: l.get("date")
                       for l in (data.get("lessons") or [])}
                marks = data.get("marks") or {}
                qoldi = {}
                for k, v in marks.items():
                    try:
                        lid, sid = (int(p) for p in k.split(":"))
                    except (ValueError, AttributeError):
                        qoldi[k] = v
                        continue
                    stop = cut.get(sid)
                    d = les.get(lid)
                    if stop is not None and d and str(d) > str(stop):
                        continue          # ketganning dumi — chiqmaydi
                    qoldi[k] = v
                data["marks"] = qoldi
                # Qatorga chegara sanasi yoziladi — UI tushuntirib
                # bersin ("15-avg dan keyin hisobga olinmaydi").
                for x in data["students"]:
                    st = cut.get(x["id"])
                    if st is not None and str(st) > "1900-01-01":
                        x["counted_until"] = str(st)
        except Exception:
            pass
        return data


# =====================================================================
#  ADMINISTRATOR ROLLARI BITTA BO'LDI
#
#  "Administrator" (sales_manager) va "Administrator (qabul)"
#  (administrator) amalda bir xil ish edi, lekin huquqlari bir xil
#  emasdi — masalan muzlatilgan o'quvchini faollashtirishni faqat
#  birinchisi qila olardi. Ekranda esa ikkalasi ham "Administrator"
#  bo'lib ko'rinardi va kim nima qila olishini hech kim bilmasdi.
#
#  2026-09-03, Jahongir: "unda shu 2ta administratorni bitta qil,
#  sales managerga birlashtir, hozirgi bor xodimlar hammasi shu admin
#  turiga o'tsin, kimdur administrator (qabul) turgan bo'lsa nargi
#  turiga o'tsin".
#
#  Uch qism:
#    1) TANLOVDAN OLIB TASHLASH — endi yangi xodimga bu rolni berib
#       bo'lmaydi (ilgari faqat ALL_ROLES tozalangan edi, tanlov
#       ro'yxatlarida esa qolib ketgan va ikkita bir xil
#       "Administrator" ko'rinardi);
#    2) MAVJUD XODIMLARNI KO'CHIRISH — asosiy rol ham, qo'shimcha
#       rollar ham (dual-role);
#    3) XAVFSIZLIK TO'RI — biror yozuv qolib ketsa ham huquqi
#       sales_manager bilan AYNAN bir xil bo'ladi.
# =====================================================================
roles.UZ_LABELS[roles.ADMINISTRATOR] = "Administrator"

# 1) Tanlov ro'yxatlaridan olib tashlaymiz.
#    DIQQAT: STAFF_ROLES ga TEGILMAYDI — u tanlov ro'yxati emas,
#    RUXSAT ro'yxati va roles.py da IDEA_SUBMIT hamda
#    SALARY_SELF_VIEW aynan o'sha obyektga ishora qiladi. Uni
#    o'zgartirsak, qolib ketgan administrator g'oya yubora olmay
#    va o'z oyligini ko'ra olmay qolardi.
roles.ALL_ROLES[:] = [r for r in roles.ALL_ROLES
                      if r != roles.ADMINISTRATOR]
for _nm2 in ("STAFF_ASSIGNABLE_ROLES", "HR_ASSIGNABLE_ROLES",
             "BRANCH_ASSIGNABLE_ROLES"):
    _cur = getattr(roles, _nm2, None)
    if isinstance(_cur, list) and roles.ADMINISTRATOR in _cur:
        setattr(roles, _nm2,
                [r for r in _cur if r != roles.ADMINISTRATOR])
for _i, _grp in enumerate(roles.ROLE_GROUPS):
    if _grp[0] == "sales":
        roles.ROLE_GROUPS[_i] = (
            _grp[0], _grp[1],
            [r for r in _grp[2] if r != roles.ADMINISTRATOR])

# 3) Qolib ketgan yozuv bo'lsa ham huquqi sales_manager bilan bir xil.
#    Quyidagi ro'yxatlarda sales_manager bor edi, administrator esa
#    yo'q — aynan shu farq "nega u qila olmayapti" degan savolni
#    keltirib chiqargan edi.
for _nm in ("ACADEMIC_VIEW", "FILL_ACCESS", "FREEZE_ROLES", "PLAN_VIEW",
            "REFUND_REQUEST", "REFUND_VIEW"):
    _v = getattr(roles, _nm, None)
    if isinstance(_v, list) and roles.SALES_MANAGER in _v \
            and roles.ADMINISTRATOR not in _v:
        _v.append(roles.ADMINISTRATOR)


def _merge_admin_roles() -> None:
    """2) Mavjud xodimlarni ko'chirish. Idempotent — ikkinchi
    chaqiruvda hech narsa qilmaydi.

    Asosiy rol ham, qo'shimcha rollar (dual-role) ham ko'chiriladi.
    Xodimda allaqachon sales_manager qo'shimcha roli bo'lsa, eski
    administrator qatori DUBL bo'lib qolmasligi uchun olib
    tashlanadi — huquqi o'sha-o'sha qoladi, hech narsa yo'qolmaydi."""
    db = _SessionLocal()
    try:
        n = (db.query(models.User)
             .filter(models.User.role == roles.ADMINISTRATOR)
             .update({models.User.role: roles.SALES_MANAGER},
                     synchronize_session=False))
        m = 0
        _UR = getattr(models, "UserRole", None)
        if _UR is not None:
            for _r in (db.query(_UR)
                       .filter(_UR.role == roles.ADMINISTRATOR).all()):
                _dup = (db.query(_UR)
                        .filter(_UR.user_id == _r.user_id,
                                _UR.role == roles.SALES_MANAGER).first())
                if _dup is not None:
                    db.delete(_r)
                else:
                    _r.role = roles.SALES_MANAGER
                m += 1
        if n or m:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


try:
    _merge_admin_roles()
except Exception:
    pass


# =====================================================================
#  XODIM OYLIGI: BERILGAN PULNI YOZIB BORISH
#  Ustozlarda TeacherPayment bor, lekin examinerda Ustoz kartasi yo'q.
#  Shuning uchun user_id'ga bog'langan umumiy jadval.
# =====================================================================
from datetime import datetime as _dt  # noqa: E402
from sqlalchemy import Column, DateTime, Float, Integer, String  # noqa: E402
from sqlalchemy import Date as _SaDate  # noqa: E402
from database import Base as _Base, engine as _engine  # noqa: E402

if getattr(models, "StaffSalaryPayment", None) is None:
    class StaffSalaryPayment(_Base):
        """Xodimga HAQIQATDA berilgan pul: oylik, avans yoki tuzatish.

        Ishlab topilgani har oy formuladan qayta hisoblanadi va hech
        qayerda saqlanmaydi; bu jadval faqat kassadan chiqqan pulni
        yozadi. Qoldiq = ishlab topgan - berilgan."""

        __tablename__ = "staff_salary_payments"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, nullable=False)
        amount = Column(Float, nullable=False)
        kind = Column(String, default="salary")
        period = Column(String, index=True)
        paid_on = Column(_SaDate, default=date.today)
        method = Column(String, default="cash")
        note = Column(String)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    models.StaffSalaryPayment = StaffSalaryPayment
    ensure_tables([StaffSalaryPayment.__table__])

_SSP = models.StaffSalaryPayment

_SALARY_KINDS = [("salary", "Oylik"), ("advance", "Avans"),
                 ("correction", "Tuzatish")]
_SALARY_KIND_LABELS = dict(_SALARY_KINDS)

# Oyliklarni Moliya bo'limida ko'radigan va to'laydiganlar
# Administrator bu ro'yxatlarda YO'Q (2026-09-16): u oylikni Xarajatlar
# -> Oylik orqali o'z filialiga beradi, hammaning oyligini ko'rmaydi.
_SALARY_PAY_ORG = [r for r in roles.SALARY_PAY
                   if r not in (roles.ADMINISTRATOR, roles.SALES_MANAGER)]
_PAYROLL_VIEW = list(dict.fromkeys(
    _SALARY_PAY_ORG + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                       roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))
_PAYROLL_PAY = list(_SALARY_PAY_ORG)


def _staff_paid(db: Session, user_id: int, period: str | None = None):
    q = db.query(func.coalesce(func.sum(_SSP.amount), 0.0)).filter(
        _SSP.user_id == user_id)
    if period:
        q = q.filter(_SSP.period == period)
    return round(float(q.scalar() or 0.0), 2)


def _attach_paid(db: Session, data: dict, key: str, period: str) -> dict:
    """Oylik ro'yxatiga "berilgan" va "qoldiq" ustunlarini qo'shadi."""
    for r in data.get("rows", []):
        uid = r.get(key)
        if uid is None:
            continue
        paid = _staff_paid(db, uid, period)
        r["paid"] = paid
        r["left"] = round((r.get("salary") or 0) - paid, 2)
    data["paid_total"] = round(
        sum(r.get("paid", 0) for r in data.get("rows", [])), 2)
    data["left_total"] = round(
        sum(r.get("left", 0) for r in data.get("rows", [])), 2)
    data["kinds"] = [{"key": k, "label": lbl} for k, lbl in _SALARY_KINDS]
    return data


# --- Examiner oyliklari: Moliya ham ko'rsin + berilgan pul ko'rinsin ---
def _rows_in_branch(db, rows, branch_id, key="user_id"):
    """Ro'yxat qatorlarini filial bo'yicha filtrlaydi (asosiy filial
    yoki qo'shimcha biriktirilgan filial mos kelsa qoladi). Filial
    tanlanganda supportlar/examinerlar ro'yxati ham faqat shu
    filialniki bo'ladi (Jahongir, 2026-08-12)."""
    if not branch_id:
        return rows
    ids = [r.get(key) for r in rows if r.get(key)]
    if not ids:
        return rows
    main_ok = {uid for (uid,) in db.query(models.User.id).filter(
        models.User.id.in_(ids),
        models.User.branch_id == branch_id).all()}
    extra_ok = {ub.user_id for ub in db.query(models.UserBranch).filter(
        models.UserBranch.user_id.in_(ids),
        models.UserBranch.branch_id == branch_id).all()}
    ok = main_ok | extra_ok
    return [r for r in rows if r.get(key) in ok]


_orig_ex_salary = _find_endpoint("/api/examiners/salary", "GET")

if _orig_ex_salary is not None:
    _drop_route("/api/examiners/salary", "GET")

    @app.get("/api/examiners/salary")
    def examiner_salary_v2(year: int | None = None, month: int | None = None,
                           branch_id: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *list(dict.fromkeys(
                                   list(roles.EXAMINER_SALARY_VIEW)
                                   + _PAYROLL_VIEW))))):
        data = _orig_ex_salary(year=year, month=month, db=db, user=user)
        if isinstance(data, dict) and data.get("rows") is not None:
            data["rows"] = _rows_in_branch(db, data["rows"], branch_id)
        data = _attach_paid(db, data, "user_id", data.get("period", ""))
        data["can_pay"] = user.role in tuple(_PAYROLL_PAY)
        return data


# --- Support teacher oyliklari: xuddi shunday ---
_orig_su_salary = _find_endpoint("/api/support/salary", "GET")

if _orig_su_salary is not None:
    _drop_route("/api/support/salary", "GET")

    @app.get("/api/support/salary")
    def support_salary_v2(year: int | None = None, month: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *list(dict.fromkeys(
                                  list(roles.SALARY_VIEW_ALL)
                                  + [roles.ACADEMIC_HEAD]
                                  + _PAYROLL_VIEW))))):
        data = _orig_su_salary(year=year, month=month, db=db, user=user)
        # Support teacherda Ustoz kartasi bor — user_id ni topib beramiz
        for r in data.get("rows", []):
            t = db.query(models.Teacher).get(r.get("teacher_id"))
            r["user_id"] = t.user_id if t else None
        data = _attach_paid(db, data, "user_id", data.get("period", ""))
        data["can_pay"] = user.role in tuple(_PAYROLL_PAY)
        return data


@app.post("/api/staff-salary")
def staff_salary_pay(payload: dict, db: Session = Depends(get_db),
                     user=Depends(require_role(*_PAYROLL_PAY))):
    """Xodimga oylik/avans berish. Bitta tugma — bitta yozuv."""
    uid = payload.get("user_id")
    amount = payload.get("amount")
    kind = payload.get("kind") or "salary"
    if not uid:
        raise HTTPException(400, "Xodim tanlanmadi")
    if kind not in _SALARY_KIND_LABELS:
        raise HTTPException(400, "Noto'g'ri to'lov turi")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        raise HTTPException(400, "Summani kiriting")
    u = db.query(models.User).get(int(uid))
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if (user.role == roles.BRANCH_MANAGER and u.branch_id
            and not M._in_user_branches(db, user, u.branch_id)):
        raise HTTPException(403, "Faqat o'z filialingiz xodimiga "
                                 "oylik bera olasiz")
    period = payload.get("period") or roles.default_pay_period(
        roles.local_today(), payload.get("kind") or "salary")
    row = _SSP(user_id=u.id, amount=round(amount, 2), kind=kind,
               period=period, paid_on=date.today(),
               method=payload.get("method") or "cash",
               note=payload.get("note"), created_by=user.full_name)
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.log(db, user, entity="user", action="salary_change",
              entity_id=u.id, entity_label=u.full_name,
              branch_id=u.branch_id,
              field=_SALARY_KIND_LABELS[kind],
              new_value=f"{amount:,.0f}".replace(",", " "))
    db.commit()
    return {"ok": True, "id": row.id,
            "paid": _staff_paid(db, u.id, period)}


@app.get("/api/staff-salary")
def staff_salary_list(user_id: int, period: str | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYROLL_VIEW))):
    q = db.query(_SSP).filter(_SSP.user_id == user_id)
    if period:
        q = q.filter(_SSP.period == period)
    rows = q.order_by(_SSP.paid_on.desc(), _SSP.id.desc()).all()
    return {
        "rows": [{"id": r.id, "amount": r.amount, "kind": r.kind,
                  "kind_label": _SALARY_KIND_LABELS.get(r.kind, r.kind),
                  "period": r.period,
                  "date": r.paid_on.isoformat() if r.paid_on else None,
                  "method": r.method, "note": r.note,
                  "created_by": r.created_by} for r in rows],
        "total": round(sum(r.amount for r in rows), 2),
        "can_pay": user.role in tuple(_PAYROLL_PAY),
    }


@app.delete("/api/staff-salary/{row_id}")
def staff_salary_delete(row_id: int, db: Session = Depends(get_db),
                        user=Depends(require_role(*_PAYROLL_PAY))):
    r = db.query(_SSP).get(row_id)
    if not r:
        raise HTTPException(404, "Topilmadi")
    u = db.query(models.User).get(r.user_id)
    audit.log(db, user, entity="user", action="delete", entity_id=r.user_id,
              entity_label=u.full_name if u else "—",
              field="Xodim oyligi",
              old_value=f"{r.amount:,.0f}".replace(",", " "))
    db.delete(r)
    db.commit()
    return {"ok": True}


# =====================================================================
#  SHU OY TO'LOV QILGANLAR RO'YXATI
#  Administrator har kuni "kim to'ladi?" deb so'raydi — endi ro'yxat
#  Moliya bo'limining o'zida turadi. Xarajat va foyda bu yerda YO'Q,
#  shuning uchun administratorga ham ochiq.
# =====================================================================
_PAYLIST_VIEW = list(dict.fromkeys([
    roles.FOUNDER, roles.BRANCH_MANAGER, roles.FINANCE_DIRECTOR,
    roles.ACCOUNTANT, roles.SALES_MANAGER, roles.ADMINISTRATOR,
]))


@app.get("/api/payments/month")
def payments_of_month(year: int | None = None, month: int | None = None,
                      branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYLIST_VIEW))):
    """Bir oyda kelib tushgan to'lovlar — o'quvchi kesimida.

    Yangi mijoz (birinchi to'lovi shu oyda) alohida belgilanadi, chunki
    administrator bonusi eski va yangi to'lov uchun boshqa-boshqa."""
    today = roles.local_today()
    y = year or today.year
    m = month or today.month
    start, end = M.billing.month_bounds(y, m)
    d0, d1 = M._utc_window(start, end)

    q = (db.query(models.Payment, models.Student)
         .join(models.Student,
               models.Payment.student_id == models.Student.id)
         .filter(models.Payment.kind == "payment",
                 models.Payment.created_at >= d0,
                 models.Payment.created_at <= d1))
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(M._branch_in(db, user, models.Student.branch_id))
    elif branch_id:
        q = q.filter(models.Student.branch_id == branch_id)

    first_dates = M._payment_first_dates(db)
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    method_labels = dict(getattr(roles, "PAYMENT_METHOD_LABELS", {}) or {})

    rows, total, new_sum, old_sum = [], 0.0, 0.0, 0.0
    for p, st in q.all():
        is_new = first_dates.get(st.id) == p.created_at
        total += p.amount
        if is_new:
            new_sum += p.amount
        else:
            old_sum += p.amount
        method = p.method or "cash"
        rows.append({
            "id": p.id,
            "date": p.created_at.date().isoformat() if p.created_at else None,
            "student_id": st.id,
            "student": st.full_name,
            "phone": st.phone,
            "amount": p.amount,
            "method": method,
            "method_label": method_labels.get(method, method),
            "branch": branches.get(st.branch_id) or "—",
            "is_new": is_new,
            "note": p.note,
            "created_by": p.created_by,
        })
    rows.sort(key=lambda r: (r["date"] or "", -r["amount"]), reverse=True)
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "count": len(rows),
        "students": len({r["student_id"] for r in rows}),
        "total": round(total, 2),
        "new_total": round(new_sum, 2),
        "old_total": round(old_sum, 2),
    }


# =====================================================================
#  LID KIRITISH: TO'LIQ TO'LDIRILSIN, FILIAL O'ZINIKI BO'LSIN
#  Bo'sh mahalla/maktab keyin hisobotni buzadi; filialni qo'lda tanlash
#  esa adashishga olib keladi — xodimning lidi o'z filialiga tushadi.
# =====================================================================
_LEAD_REQUIRED = [
    ("full_name", "Ism-familiya"),
    ("phone", "Telefon"),
    ("address", "Qayerdan (mahalla / tuman)"),
    ("school", "Maktab"),
    ("grade", "Sinf"),
    ("source", "Qayerdan keldi"),
]

_cur_create_lead = _find_endpoint("/api/leads", "POST")

if _cur_create_lead is not None:
    _drop_route("/api/leads", "POST")

    @app.post("/api/leads", response_model=schemas.LeadOut)
    def create_lead_v2(payload: schemas.LeadCreate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        missing = []
        for field, label in _LEAD_REQUIRED:
            val = (getattr(payload, field, None) or "")
            if field == "phone":
                digits = "".join(c for c in str(val) if c.isdigit())
                if len(digits) < 9:
                    missing.append(label)
            elif not str(val).strip():
                missing.append(label)
        if missing:
            raise HTTPException(
                400, "Quyidagilar to'ldirilmadi: " + ", ".join(missing))

        # Filiali bor xodim boshqa filialga lid yoza olmaydi
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            payload.branch_id = user.branch_id
        elif not payload.branch_id:
            payload.branch_id = user.branch_id
        if not payload.branch_id:
            raise HTTPException(400, "Filial tanlanmadi")

        return _cur_create_lead(payload=payload, db=db, user=user)


# =====================================================================
#  OYLIK HISOB-KITOB: JADVALNI O'ZI YARATIB, HAMMADAN BIRDAN YECHADI
#  Eski xatolik: dars kunlari faqat kimdir guruh yo'qlamasini ochganda
#  yaratilardi. Yangi guruhda hech kim ochmagan bo'lsa "0 dars" chiqib,
#  hech kimdan pul yechilmasdi. Endi hisoblashdan oldin jadval o'zi
#  to'ldiriladi.
#
#  whole_month=True — o'quvchi oy o'rtasida qo'shilgan bo'lsa ham
#  to'liq oy uchun hisoblanadi (eski o'quvchilarni ro'yxatga endi
#  kiritganda kerak bo'ladi).
# =====================================================================
_drop_route("/api/billing/month", "POST")


@app.post("/api/billing/month")
def billing_month_v2(year: int, month: int, commit: bool = False,
                     whole_month: bool = False,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    period = M._period_key(year, month)
    start, end = M.billing.month_bounds(year, month)

    students = [s for s in scope_to_branch(
        db.query(models.Student), models.Student, user).all()
        if s.status == "active" and s.group_id]

    # Avval jadvalni to'ldiramiz — har guruh uchun bir marta
    synced = set()
    for s in students:
        g = s.group
        if not g or g.id in synced:
            continue
        synced.add(g.id)
        try:
            M._sync_scheduled_lessons(db, g, start, end)
        except Exception:
            db.rollback()
    if synced:
        db.commit()

    rows, created, no_lesson = [], 0, 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        since = start
        if not whole_month and s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        lessons = (len(M._lessons_left_in_month(db, g.id, since))
                   if since <= end else 0)
        disc = M._student_discount_percent(db, s)
        amount = lessons * _billing.student_lesson_price(s, g) \
            * (100 - disc) / 100
        if lessons == 0:
            no_lesson += 1

        if commit and not already and amount > 0 \
                and not M._charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (chegirma {disc}%)" if disc else ""),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": lessons, "discount": disc,
            "amount": round(amount, 2),
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
        "no_lesson": no_lesson,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }


# =====================================================================
#  NARX SIYOSATI: OYIGA 12 DARS = 480 000 SO'M
#  Bitta dars 40 000. Oyda 13-14 dars chiqsa, ortig'i BONUS — mijozdan
#  baribir 12 dars uchun olinadi. Oy o'rtasida qo'shilgan o'quvchi esa
#  faqat qolgan darslari uchun to'laydi (u ham 12 tadan oshmaydi).
#
#  Diqqat: bu faqat O'QUVCHI to'lovi. Ustoz oyligi yo'qlamadan
#  hisoblanadi va bu yerga aloqasi yo'q — tegilmadi.
# =====================================================================
def _lesson_cap(g) -> int:
    return int(getattr(g, "standard_lessons_per_month", None) or 12)


def _billable_lessons(db, g, since, start, end) -> int:
    """Mijozdan haqiqatda olinadigan darslar soni.

    To'liq oy o'qiydigan o'quvchi standart 12 darsni to'laydi — kalendarda
    13 chiqsa ham, 11 chiqsa ham. Oy o'rtasida qo'shilgan (yoki guruhi
    oy o'rtasida ochilgan) bo'lsa — o'sha kundan oy oxirigacha nechta
    dars bo'lsa, shuncha (lekin 12 tadan oshmaydi)."""
    cap = _lesson_cap(g)
    partial = since > start
    if getattr(g, "start_date", None) and g.start_date > start:
        partial = True
    if getattr(g, "end_date", None) and g.end_date < end:
        partial = True
    if not partial:
        return cap
    n = len(M._lessons_left_in_month(db, g.id, since)) if since <= end else 0
    return min(n, cap)


def _charge_note(g, period: str, billable: int, disc: float,
                 prefix: str = "") -> str:
    cap = _lesson_cap(g)
    txt = f"{g.name} — {period}: {prefix}{billable} dars"
    if billable >= cap:
        txt += " (standart oy)"
    if disc:
        txt += f" (chegirma {disc}%)"
    return txt


# --- Faollashtirilganda avtomat yechish ham shu qoidaga bo'ysunsin ---
def _charge_from_activation_v2(db, s, since, user=None, honor_skip=True):
    """Faollashgan kundan oy oxirigacha — 12 darsdan oshmaydi.

    honor_skip=False (2026-09-28): FAOLLASHISH paytida asoschining
    o'sha oy uchun o'chirgan yechimi (ChargeSkip) to'siq emas. U
    o'quvchi kelmay turgan HOLATga tegishli edi; o'quvchi qaytib
    kelganda qaytgan kunidan dars pulini to'laydi. Ilgari skip
    faollashish yechimini ham butunlay to'sardi — o'quvchi oy oxirigacha
    tekin o'qib qolardi (Aloviddinov Asadbek: 11-sentabr "sentabr
    kelmagan" deb o'chirilgan, 23-sentabr qaytdi, pul yechilmadi)."""
    if not s.group_id or not s.group:
        return None
    period = M._period_key(since.year, since.month)
    exists = (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.period == period,
                      models.Payment.kind == "charge").first())
    if exists:
        return None
    if honor_skip and M._charge_skipped(db, s.id, period):
        return None

    start, end = M.billing.month_bounds(since.year, since.month)
    g = s.group
    # Guruh jadvali hali yaratilmagan bo'lsa — o'zi to'ldiradi
    try:
        M._sync_scheduled_lessons(db, g, start, end)
    except Exception:
        pass
    n = _billable_lessons(db, g, since, start, end)
    if n <= 0:
        return None

    price = _billing.student_lesson_price(s, g)   # eski narx himoyasi
    disc = M._student_discount_percent(db, s)
    amount = n * price * (100 - disc) / 100
    if amount <= 0:
        return None

    db.add(models.Payment(
        student_id=s.id, amount=-abs(amount), kind="charge",
        note=_charge_note(g, period, n, disc, "faollashgandan "),
        created_by=(user.full_name if user else "avtomat"),
        period=period))
    return {"lessons": n, "amount": amount, "discount": disc}


def _charge_months_after(db, s, since, user=None) -> list:
    """Faollashish oyidan KEYINGI oylar (joriy oygacha) — yechilmagan
    bo'lsa, to'liq standart oylik (2026-09-16, Jahongir: "faol
    qilganingda faollashtirilgan kundan boshlab oylik tolovni yechib
    olish kerak, bazi o'quvchilar faol bolsa ham pul yechilmayabdi").

    Nega kerak: sinov darsi o'tgan oyda boshlanib, 3-darsi shu oyga
    tushsa, faollashish sanasi — o'tgan oy. Shu oyning 1-kunidagi
    avtomat yechimda esa o'quvchi hali sinovda edi. Natijada faqat
    o'tgan oy yechilib, shu oy butunlay yechilmay qolardi."""
    if not s.group_id or not s.group:
        return []
    today = roles.local_today()
    g = s.group
    std = int(g.standard_lessons_per_month or 12) or 12
    y, m = since.year, since.month
    out = []
    while True:
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if (y, m) > (today.year, today.month):
            break
        period = M._period_key(y, m)
        if period < _MC_FROM:
            continue
        if _mc_has_charge(db, s.id, period) or M._charge_skipped(db, s.id, period):
            continue
        full = _mc_after_discount(
            db, s, roles.money(_billing.student_lesson_price(s, g) * std))
        if full <= 0:
            continue
        db.add(models.Payment(
            student_id=s.id, amount=-full, kind="charge",
            note=f"{g.name} — {period}: {std} dars (standart oy, faollashganda)",
            created_by=_MC_BY, period=period))
        out.append({"period": period, "amount": full, "lessons": std})
    return out


def _charge_from_activation_v3(db, s, since, user=None):
    """Faollashgan kundan shu oy oxirigacha (v2) + keyingi yechilmagan
    oylar joriy oygacha.

    Faollashish oyi uchun ChargeSkip hisobga olinmaydi (v2 izohiga
    qarang, 2026-09-28) — bu funksiya faqat HOLAT faolga o'tganda
    chaqiriladi. Keyingi oylarda esa asoschining o'chirishi hurmat
    qilinadi (_charge_months_after)."""
    res = _charge_from_activation_v2(db, s, since, user, honor_skip=False)
    extra = _charge_months_after(db, s, since, user)
    if not extra:
        return res
    base = res or {"lessons": 0, "amount": 0.0, "discount": 0}
    return {
        "lessons": base["lessons"] + sum(x["lessons"] for x in extra),
        "amount": base["amount"] + sum(x["amount"] for x in extra),
        "discount": base.get("discount", 0),
        "months": ([since.isoformat()[:7]] if res else [])
                  + [x["period"] for x in extra],
    }


M._charge_from_activation = _charge_from_activation_v3


# --- Oylik hisob-kitob ---
_drop_route("/api/billing/month", "POST")


@app.post("/api/billing/month")
def billing_month_v3(year: int, month: int, commit: bool = False,
                     whole_month: bool = False,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    period = M._period_key(year, month)
    start, end = M.billing.month_bounds(year, month)

    students = [s for s in scope_to_branch(
        db.query(models.Student), models.Student, user).all()
        if s.status == "active" and s.group_id]

    # Jadvalni avval to'ldiramiz — har guruh uchun bir marta
    synced = set()
    for s in students:
        g = s.group
        if not g or g.id in synced:
            continue
        synced.add(g.id)
        try:
            M._sync_scheduled_lessons(db, g, start, end)
        except Exception:
            db.rollback()
    if synced:
        db.commit()

    rows, created, no_lesson = [], 0, 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        since = start
        if not whole_month and s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        billable = _billable_lessons(db, g, since, start, end)
        disc = M._student_discount_percent(db, s)
        amount = billable * _billing.student_lesson_price(s, g) \
            * (100 - disc) / 100
        if billable == 0:
            no_lesson += 1

        if commit and not already and amount > 0 \
                and not M._charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=_charge_note(g, period, billable, disc),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": billable, "discount": disc,
            "amount": round(amount, 2),
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
        "no_lesson": no_lesson,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }


# =====================================================================
#  FAOLLASHTIRISH: SANA SO'RALADI VA O'SHA KUNDAN PUL YECHILADI
#  Administrator "Faollashtirish" bosganda qaysi kundan o'qishni
#  boshlaganini kiritadi. Shu kundan oy oxirigacha nechta dars bo'lsa,
#  40 000 dan ko'paytirib avtomat yechiladi (12 darsdan oshmaydi).
# =====================================================================
_drop_route("/api/students/{student_id}/activate", "POST")


@app.post("/api/students/{student_id}/activate")
def activate_student_v2(student_id: int, payload: dict | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FREEZE_ROLES))):
    # FILIAL CHEGARASI (2026-09-06 auditi)
    s = M._get_student_in_scope(db, student_id, user)
    if s.status == "active":
        raise HTTPException(400, "Bu o'quvchi allaqachon faol")

    on = M.roles.local_today()
    raw = (payload or {}).get("on")
    if raw:
        try:
            on = date.fromisoformat(str(raw)[:10])
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")
    if on > M.roles.local_today():
        raise HTTPException(400, "Kelajakdagi sanani tanlab bo'lmaydi")

    old = s.status
    s.status = "active"
    if not s.enrolled_date or s.enrolled_date > on:
        s.enrolled_date = on
    M._sync_student_left_date(s)

    charge = _charge_from_activation_v2(db, s, on, user)

    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old, new_value="active", branch_id=s.branch_id,
              note=(f"{on.isoformat()} dan — {charge['lessons']} dars, "
                    f"{charge['amount']:,.0f} so'm".replace(",", " ")
                    if charge else on.isoformat()))
    db.commit()
    return {"ok": True, "status": s.status,
            "activated_on": on.isoformat(), "charge": charge}


@app.get("/api/students/{student_id}/activate-preview")
def activate_preview(student_id: int, on: str | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faollashtirishdan oldin: shu sanadan qancha pul yechilishini
    ko'rsatadi — administrator tasdiqlashdan oldin ko'rib turadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    day = M.roles.local_today()
    if on:
        try:
            day = date.fromisoformat(str(on)[:10])
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")
    g = s.group
    if not g:
        return {"lessons": 0, "amount": 0, "discount": 0,
                "already": False, "group": None,
                "hint": "O'quvchi guruhga biriktirilmagan — pul "
                        "hisoblanmaydi."}
    start, end = M.billing.month_bounds(day.year, day.month)
    try:
        M._sync_scheduled_lessons(db, g, start, end)
        db.commit()
    except Exception:
        db.rollback()
    period = M._period_key(day.year, day.month)
    already = (db.query(models.Payment)
               .filter(models.Payment.student_id == s.id,
                       models.Payment.period == period,
                       models.Payment.kind == "charge").first()) is not None
    n = _billable_lessons(db, g, day, start, end)
    disc = M._student_discount_percent(db, s)
    _pr = _billing.student_lesson_price(s, g)     # eski narx himoyasi
    amount = n * _pr * (100 - disc) / 100
    cap = _lesson_cap(g)
    return {
        "lessons": n, "amount": round(amount, 2), "discount": disc,
        "already": already, "group": g.name,
        "lesson_price": _pr, "cap": cap,
        "hint": ("Bu oy uchun allaqachon hisoblangan — qayta yechilmaydi."
                 if already else
                 f"{n} dars x {_pr:,.0f} so'm"
                 .replace(",", " ")
                 + (f" (chegirma {disc}%)" if disc else "")),
    }


# =====================================================================
#  LC UP'DAN ESKI TO'LOVLAR TARIXINI KO'CHIRISH
#  Har bir eski to'lov yoniga o'sha kunning "hisoblangan" yozuvi ham
#  qo'yiladi — natijada BALANS O'ZGARMAYDI. Ya'ni tarix ko'rinadi,
#  lekin bugungi qarz buzilmaydi.
#
#  Barcha yozuvlar izohida "[LC UP]" belgisi turadi — kerak bo'lsa
#  bitta tugma bilan hammasini qaytarib olib tashlash mumkin.
# =====================================================================
_LCUP_TAG = "[LC UP]"
_IMPORT_ROLES = list(dict.fromkeys(
    list(roles.FINANCE_ACCESS) + [roles.FOUNDER]))


def _norm_name(s) -> str:
    t = (s or "").lower().replace("'", "'").replace("`", "'")
    t = _re2.sub(r"[^a-z0-9а-яё ]+", " ", t)
    return " ".join(t.split())


def _phone_tail(s) -> str:
    d = "".join(ch for ch in str(s or "") if ch.isdigit())
    return d[-9:] if len(d) >= 9 else ""


def _parse_money(v) -> float:
    """"480 000", "480,000.00", "480000 so'm" — hammasi 480000 bo'ladi."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(" ", " ")
    t = _re2.sub(r"[^0-9,.\-]", "", t)
    if not t:
        return 0.0
    # 1,234.56 -> nuqta kasr; 1.234,56 -> vergul kasr
    if "," in t and "." in t:
        t = (t.replace(",", "") if t.rfind(".") > t.rfind(",")
             else t.replace(".", "").replace(",", "."))
    elif "," in t:
        t = t.replace(",", "" if len(t.split(",")[-1]) == 3 else ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def _parse_day(v):
    """2026-08-07, 07.08.2026, 07/08/2026 — hammasini tushunadi."""
    if not v:
        return None
    if isinstance(v, date):
        return v
    t = str(v).strip()[:19].replace("T", " ")
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return _dt.strptime(t[:len(_dt.now().strftime(fmt))], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(t[:10])
    except ValueError:
        return None


_METHOD_WORDS = {
    "cash": ("naqd", "cash", "нал"),
    "card": ("click", "karta", "card", "payme", "uzum", "plastik"),
    "terminal": ("terminal", "терминал", "pos"),
}


def _parse_method(v) -> str:
    t = str(v or "").lower()
    for key, words in _METHOD_WORDS.items():
        if any(w in t for w in words):
            return key
    return "cash"


def _student_index(db, user):
    """Ism va telefon bo'yicha o'quvchi qidirish uchun indeks."""
    q = scope_to_branch(db.query(models.Student), models.Student, user)
    by_name, by_phone = {}, {}
    for s in q.all():
        n = _norm_name(s.full_name)
        if n:
            by_name.setdefault(n, []).append(s)
        for ph in (s.phone, s.parent_phone):
            t = _phone_tail(ph)
            if t:
                by_phone.setdefault(t, []).append(s)
    return by_name, by_phone


# Diqqat: /api/payments/{id} yo'li bilan to'qnashmasin uchun
# alohida prefiks.
@app.post("/api/lcup/payments")
def import_payments(payload: dict, db: Session = Depends(get_db),
                    user=Depends(require_role(*_IMPORT_ROLES))):
    """LC UP eksportidan eski to'lovlarni ko'chiradi.

    commit=false — faqat tekshirib ko'rsatadi, hech narsa yozmaydi."""
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    by_name, by_phone = _student_index(db, user)
    # Takror importni ushlash uchun: allaqachon bor [LC UP] to'lovlari
    seen = set()
    for p in (db.query(models.Payment)
              .filter(models.Payment.kind == "payment",
                      models.Payment.note.like(f"%{_LCUP_TAG}%")).all()):
        seen.add((p.student_id, p.created_at.date() if p.created_at else None,
                  round(p.amount, 2)))

    out, ok, dup, miss, total = [], 0, 0, 0, 0.0
    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        amount = _parse_money(r.get("amount"))
        day = _parse_day(r.get("date"))
        phone = _phone_tail(r.get("phone"))

        if not name and not phone:
            continue
        if amount <= 0:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "summa yo'q yoki noto'g'ri"})
            continue
        if not day:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "sana o'qilmadi"})
            continue

        # Avval ism, keyin telefon; ikkalasi bo'lsa — ikkovi kesishgani
        cands = list(by_name.get(_norm_name(name), []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in cands if s in ph]
            if both:
                cands = both
            elif not cands:
                cands = list(ph)
        if not cands:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "not_found",
                        "reason": "bunday o'quvchi topilmadi"})
            continue
        if len(cands) > 1:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "ambiguous",
                        "reason": f"{len(cands)} ta bir xil ismli o'quvchi "
                                  f"bor — telefon ustunini qo'shing"})
            continue

        s = cands[0]
        key = (s.id, day, round(amount, 2))
        if key in seen:
            dup += 1
            out.append({"row": i + 1, "name": s.full_name,
                        "date": day.isoformat(), "amount": amount,
                        "status": "duplicate",
                        "reason": "bu to'lov allaqachon ko'chirilgan"})
            continue
        seen.add(key)

        method = _parse_method(r.get("method"))
        note = str(r.get("note") or "").strip()
        total += amount
        ok += 1
        out.append({"row": i + 1, "name": s.full_name, "student_id": s.id,
                    "date": day.isoformat(), "amount": amount,
                    "method": method, "status": "ok"})

        if commit:
            when = _dt.combine(day, _dt.min.time())
            tail = f" · {note}" if note else ""
            # To'lov (plyus)
            db.add(models.Payment(
                student_id=s.id, amount=abs(amount), kind="payment",
                method=method, created_at=when, period=None,
                note=f"{_LCUP_TAG} eski to'lov{tail}",
                created_by=user.full_name))
            # O'sha kunning hisoblangani (minus) — balans o'zgarmasin
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                created_at=when, period=None,
                note=f"{_LCUP_TAG} eski hisob ({day.strftime('%Y-%m')})",
                created_by=user.full_name))

    if commit and ok:
        db.commit()
        audit.log(db, user, entity="payment", action="import",
                  entity_label=f"LC UP: {ok} ta eski to'lov",
                  new_value=ok,
                  note=f"jami {total:,.0f} so'm".replace(",", " "),
                  commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "not_found": miss, "total": round(total, 2),
            "rows": out[:500], "shown": min(len(out), 500),
            "all_rows": len(out)}


@app.post("/api/lcup/cleanup-august")
def lcup_cleanup_august(payload: dict = Body(default={}),
                        db: Session = Depends(get_db),
                        user=Depends(require_role(roles.FOUNDER))):
    """AVGUST DUBL YECHIMINI TOZALASH (2026-08-22).

    Jahongir: "JonyOSda ikki marta avgust uchun yechganlarni ochirsang
    balans tenglashadiganlari bor. Masalan tolovlarni kirgizganimda sen
    balansni tenglashtirish uchun o'zingcha yana yechib olishlar
    qilgansan shularni ochir, hammasidan avgust oyi uchun yechilgan
    pul".

    Nima bo'lgan edi: LC UP to'lov importi har eski to'lov YONIGA xuddi
    shu summada "[LC UP] eski hisob (YYYY-MM)" yechimini ham yozadi —
    eski tarix balansni buzmasin deb (netto nol). Lekin 2026-08 uchun
    JonyOS AVTOMAT oylikni allaqachon yechib bo'lgan — natijada avgust
    IKKI MARTA yechilgan bo'lib qoldi.

    Bu endpoint faqat shunday DUBL holatlarni topadi: o'quvchida ham
    "[LC UP] eski hisob (2026-08)" yechimi, ham 2026-08 davri uchun
    avtomat oylik bo'lsa — import yechimi ARXIVGA ko'chiriladi
    (payments_deleted, tiklash mumkin). Hech narsa yo'q qilinmaydi.
    commit=false — faqat ko'rib chiqish."""
    commit = bool(payload.get("commit"))

    charges = (db.query(models.Payment)
               .filter(models.Payment.kind == "charge",
                       models.Payment.note.like(
                           f"%{_LCUP_TAG} eski hisob (2026-08)%"))
               .all())
    sids = list({c.student_id for c in charges})
    if not sids:
        return {"rows": [], "count": 0, "total": 0.0, "committed": False}

    # Shu o'quvchilardan qaysilarida 2026-08 uchun AVTOMAT oylik bor
    auto = {sid for (sid,) in
            db.query(models.Payment.student_id)
            .filter(models.Payment.kind == "charge",
                    models.Payment.period == "2026-08",
                    models.Payment.student_id.in_(sids))
            .distinct().all()}
    students = {st.id: st for st in
                db.query(models.Student)
                .filter(models.Student.id.in_(sids)).all()}

    rows, total = [], 0.0
    victims = []
    for c in charges:
        if c.student_id not in auto:
            continue        # dubl emas — avto oylik yo'q, tegilmaydi
        st = students.get(c.student_id)
        rows.append({
            "payment_id": c.id, "student_id": c.student_id,
            "student": st.full_name if st else c.student_id,
            "amount": c.amount,
            "date": c.created_at.date().isoformat()
                    if c.created_at else None,
            "note": c.note,
        })
        total += abs(c.amount)
        victims.append(c)

    if commit and victims:
        st_by_id = students
        for c in victims:
            st = st_by_id.get(c.student_id)
            db.add(models.DeletedPayment(
                payment_id=c.id, public_id=c.public_id,
                student_id=c.student_id,
                student_name=st.full_name if st else None,
                branch_id=st.branch_id if st else None,
                amount=c.amount, kind=c.kind, method=c.method,
                note=c.note, period=c.period, created_by=c.created_by,
                created_at=c.created_at,
                entered_at=getattr(c, "entered_at", None),
                client_key=getattr(c, "client_key", None),
                deleted_by=user.full_name,
                reason="Avgust dubl yechimi: avto oylik + LC UP import "
                       "yechimi birga tushib qolgan edi"))
            db.delete(c)
        audit.log(db, user, entity="payment", action="debt_write_off",
                  entity_label=f"LC UP avgust dubl tozalash: "
                               f"{len(victims)} ta yechim arxivga",
                  old_value=round(total, 2), new_value=None,
                  note="Jahongir buyrug'i: avgust ikki marta "
                       "yechilganlarni tozalash (2026-08-22)")
        db.commit()

    return {"rows": rows[:600], "count": len(rows),
            "total": round(total, 2), "committed": bool(commit and victims)}


@app.post("/api/lcup/cleanup-august-undo-pre12")
def lcup_cleanup_undo_pre12(payload: dict = Body(default={}),
                            db: Session = Depends(get_db),
                            user=Depends(require_role(roles.FOUNDER))):
    """TOZALASHNING ORTIQCHA QISMINI QAYTARISH (2026-08-22).

    Dubl tozalashda 11-avgustGAcha sanali juft yechimlar ham arxivga
    ketgan edi. Lekin o'sha kunlardagi to'lovlar 11-avgustdagi
    "balans tenglashtirish"da ALLAQACHON hisoblangan — juft yechimi
    o'chirilsa balans +to'lovcha oshib ketadi (LC UPdan yuqori).

    Bu endpoint bugungi tozalash arxividan created_at < 2026-08-12
    bo'lgan yechimlarni topib, FAQAT tenglashtirish qatnashgan
    o'quvchilar uchun QAYTARIB qo'yadi (mavjud restore mexanizmi
    mantig'i bilan). commit=false — ko'rib chiqish."""
    from datetime import datetime as _dtm
    commit = bool(payload.get("commit"))
    cut = _dtm(2026, 8, 12)

    arch = (db.query(models.DeletedPayment)
            .filter(models.DeletedPayment.reason.like("Avgust dubl%"),
                    models.DeletedPayment.restored_at.is_(None),
                    models.DeletedPayment.created_at < cut).all())
    sids = list({a.student_id for a in arch})
    if not sids:
        return {"rows": [], "count": 0, "total": 0.0, "committed": False}
    teng = {sid for (sid,) in
            db.query(models.Payment.student_id)
            .filter(models.Payment.kind == "payment",
                    models.Payment.note.like("%balans tenglashtirish%"),
                    models.Payment.student_id.in_(sids))
            .distinct().all()}

    rows, total = [], 0.0
    victims = []
    for a in arch:
        if a.student_id not in teng:
            continue    # tenglashtirishda qatnashmagan — qaytarilmaydi
        rows.append({"archive_id": a.id, "student": a.student_name,
                     "amount": a.amount,
                     "date": a.created_at.date().isoformat()
                             if a.created_at else None})
        total += abs(a.amount)
        victims.append(a)

    if commit and victims:
        now = _dtm.utcnow()
        for a in victims:
            db.add(models.Payment(
                student_id=a.student_id, amount=a.amount, kind=a.kind,
                method=a.method, note=a.note, period=a.period,
                created_by=a.created_by, created_at=a.created_at))
            a.restored_at = now
            a.restored_by = user.full_name
        audit.log(db, user, entity="payment", action="update",
                  entity_label=f"Avgust dubl tozalash tuzatildi: "
                               f"{len(victims)} ta 12-avggacha yechim "
                               f"qaytarildi (tenglashtirish qatnashgan)",
                  new_value=round(total, 2))
        db.commit()

    return {"rows": rows[:600], "count": len(rows),
            "total": round(total, 2), "committed": bool(commit and victims)}


@app.get("/api/lcup/payments")
def import_payments_stats(db: Session = Depends(get_db),
                          user=Depends(require_role(*_IMPORT_ROLES))):
    """Hozirgacha nechta eski to'lov ko'chirilgan."""
    q = (db.query(models.Payment)
         .filter(models.Payment.kind == "payment",
                 models.Payment.note.like(f"%{_LCUP_TAG}%")))
    rows = q.all()
    return {"count": len(rows),
            "total": round(sum(r.amount for r in rows), 2),
            "first": min((r.created_at.date().isoformat()
                          for r in rows if r.created_at), default=None),
            "last": max((r.created_at.date().isoformat()
                         for r in rows if r.created_at), default=None)}


@app.delete("/api/lcup/payments")
def import_payments_undo(db: Session = Depends(get_db),
                         user=Depends(require_role(roles.FOUNDER))):
    """Ko'chirilgan hammasini qaytarib olib tashlaydi — faqat asoschi."""
    n = (db.query(models.Payment)
         .filter(models.Payment.note.like(f"%{_LCUP_TAG}%"))
         .delete(synchronize_session=False))
    db.commit()
    audit.log(db, user, entity="payment", action="delete",
              entity_label="LC UP importi bekor qilindi",
              old_value=n, commit=True)
    return {"deleted": n}


# =====================================================================
#  HR MENEJERGA YANA UCHTA HUQUQ
#  Dars ko'chirish (kelmagan kunni surish ham shu), coin qo'shish va
#  tahrirlash. Eski yo'qlama allaqachon ochilgan.
#
#  RESCHEDULE_APPROVE'ga HR_MANAGER qo'shish endi faylning ENG
#  BOSHIDA ham bajariladi (qarang: yuqorida, _drop_route() ta'rifidan
#  keyin) - bu yerdagi qator shunchaki xavfsizlik uchun qoldirilgan
#  (if tekshiruvi tufayli ikki marta qo'shib yubormaydi).
# =====================================================================
if _HRM not in roles.RESCHEDULE_APPROVE:
    roles.RESCHEDULE_APPROVE.append(_HRM)
if _HRM not in roles.COIN_ADMIN:
    roles.COIN_ADMIN.append(_HRM)
try:
    roles.DEFAULT_MATRIX[_HRM]["gamification"] = {"view", "edit"}
except Exception:
    pass

_TEACH_HR = tuple(dict.fromkeys(tuple(roles.TEACHING_ACCESS) + (_HRM,)))

# --- Dars ko'chirish ---
_cur_reschedule = _find_endpoint("/api/groups/{gid}/reschedule", "POST")

if _cur_reschedule is not None:
    _drop_route("/api/groups/{gid}/reschedule", "POST")

    @app.post("/api/groups/{gid}/reschedule")
    def group_reschedule_v2(gid: int, payload: schemas.GroupRescheduleIn,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*_TEACH_HR))):
        return _cur_reschedule(gid=gid, payload=payload, db=db, user=user)


# --- Coin qo'shish / o'chirish ---
_cur_coin_add = _find_endpoint("/api/students/{student_id}/coins", "POST")
_cur_coin_del = _find_endpoint("/api/coins/{entry_id}", "DELETE")

if _cur_coin_add is not None:
    _drop_route("/api/students/{student_id}/coins", "POST")

    @app.post("/api/students/{student_id}/coins",
              response_model=schemas.CoinEntryOut)
    def add_manual_coins_v2(student_id: int, payload: schemas.CoinManual,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*roles.COIN_ADMIN))):
        return _cur_coin_add(student_id=student_id, payload=payload,
                             db=db, user=user)

if _cur_coin_del is not None:
    _drop_route("/api/coins/{entry_id}", "DELETE")

    @app.delete("/api/coins/{entry_id}")
    def delete_coin_entry_v2(entry_id: int, db: Session = Depends(get_db),
                             user=Depends(require_role(*roles.COIN_ADMIN))):
        return _cur_coin_del(entry_id=entry_id, db=db, user=user)


# =====================================================================
#  BAHO QO'YISH QOIDALARI QAT'IYLASHDI
#  1) Yo'qlama qo'yilmagan o'quvchiga baho qo'yib bo'lmaydi — aks holda
#     darsga kelmagan bolaga coin tushib ketardi.
#  2) O'tib ketgan kunga baho qo'yish yopiq (yo'qlama bilan bir xil
#     qoida): faqat asoschi, o'quv bo'limi rahbari va HR.
#  3) Hali kelmagan kunga ham baho yo'q.
# =====================================================================
_cur_save_grades = _find_endpoint("/api/lessons/{lesson_id}/grades", "PUT")

if _cur_save_grades is not None:
    _drop_route("/api/lessons/{lesson_id}/grades", "PUT")

    @app.put("/api/lessons/{lesson_id}/grades")
    def save_grades_v2(lesson_id: int, payload: schemas.GradeBulk,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.GRADE_EDIT))):
        lesson = db.query(models.Lesson).get(lesson_id)
        if not lesson:
            raise HTTPException(404, "Dars topilmadi")
        _get_group_in_scope(db, lesson.group_id, user)

        today = M.roles.local_today()
        if lesson.date > today:
            raise HTTPException(
                400, "Hali kelmagan kunga baho qo'yilmaydi — dars "
                     "bo'lib o'tmagan")
        if lesson.date < today and user.role not in tuple(
                roles.PAST_ATTENDANCE):
            raise HTTPException(
                403, "O'tib ketgan kunga baho qo'yib bo'lmaydi. Kerak "
                     "bo'lsa o'quv bo'limi rahbari yoki HR menejerga "
                     "murojaat qiling")

        # Yo'qlamasi yo'q (yoki kelmagan) o'quvchiga baho yo'q
        att = {a.student_id: (a.present or 0) for a in
               db.query(models.Attendance)
               .filter(models.Attendance.lesson_id == lesson_id).all()}
        for m in payload.marks:
            if m.score is None:
                continue          # bahoni olib tashlash har doim mumkin
            state = att.get(m.student_id)
            if state is None:
                st = db.query(models.Student).get(m.student_id)
                raise HTTPException(
                    400, f"Avval yo'qlama qo'ying — "
                         f"{st.full_name if st else 'o?quvchi'} uchun bu "
                         f"darsda belgi yo'q")
            if state == 0:
                st = db.query(models.Student).get(m.student_id)
                raise HTTPException(
                    400, f"{st.full_name if st else 'O?quvchi'} bu darsga "
                         f"kelmagan — kelmagan o'quvchiga baho ham, coin "
                         f"ham qo'yilmaydi")

        return _cur_save_grades(lesson_id=lesson_id, payload=payload,
                                db=db, user=user)


# --- Baho jadvali: qaysi katakka tegish mumkinligi ham qaytsin ---
_cur_grade_grid = _find_endpoint("/api/groups/{group_id}/grades", "GET")

if _cur_grade_grid is not None:
    _drop_route("/api/groups/{group_id}/grades", "GET")

    @app.get("/api/groups/{group_id}/grades")
    def grade_grid_v2(group_id: int, year: int, month: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.ATTENDANCE_VIEW))):
        res = _cur_grade_grid(group_id=group_id, year=year, month=month,
                              db=db, user=user)
        try:
            data = res.model_dump()
        except AttributeError:
            try:
                data = res.dict()
            except AttributeError:
                data = dict(res)
        ids = [ls["id"] for ls in data.get("lessons", [])]
        present = {}
        if ids:
            for a in (db.query(models.Attendance)
                      .filter(models.Attendance.lesson_id.in_(ids)).all()):
                present[f"{a.lesson_id}:{a.student_id}"] = int(a.present or 0)
        today = M.roles.local_today()
        data["present"] = present
        data["can_past"] = user.role in tuple(roles.PAST_ATTENDANCE)
        data["today"] = today.isoformat()
        return data


# =====================================================================
#  O'QUVCHINI USTOZ TAHRIRLAY OLMASIN
#  Ustoz dars beradi, o'quvchi kartasini esa administrator yuritadi.
#  Ko'rish qoladi, faqat saqlash yopiladi.
# =====================================================================
_NO_EDIT = (roles.TEACHER, roles.SUPPORT_TEACHER)
_STUDENT_EDIT = tuple(r for r in
                      (tuple(roles.TEACHING_STAFF) + (_HRM,))
                      if r not in _NO_EDIT)

_cur_upd_student = _find_endpoint("/api/students/{student_id}", "PUT")

if _cur_upd_student is not None:
    _drop_route("/api/students/{student_id}", "PUT")

    @app.put("/api/students/{student_id}", response_model=schemas.StudentOut)
    def update_student_v3(student_id: int, payload: schemas.StudentUpdate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*_STUDENT_EDIT))):
        return _cur_upd_student(student_id=student_id, payload=payload,
                                force=force, db=db, user=user)


# =====================================================================
#  GURUH VA FILIAL ALMASHTIRISH
#  "Boshqa guruhga o'tkazish" — faqat O'SHA FILIAL ichida. Filialni
#  almashtirish alohida amal: u yerdagi administratorga vazifa tushadi,
#  chunki o'quvchini kutib olish, shartnoma va to'lov unga o'tadi.
# =====================================================================
def _branch_admin(db, branch_id):
    """Filialdagi administrator (bo'lmasa — filial rahbari)."""
    if not branch_id:
        return None
    q = db.query(models.User).filter(models.User.is_active == 1,
                                     models.User.branch_id == branch_id)
    for wanted in (_ADMIN_ROLES, (roles.BRANCH_MANAGER,)):
        u = q.filter(models.User.role.in_(wanted)).order_by(
            models.User.id).first()
        if u:
            return u
    return None


_cur_move_group = _find_endpoint("/api/students/{student_id}/move-group",
                                 "POST")

if _cur_move_group is not None:
    _drop_route("/api/students/{student_id}/move-group", "POST")

    @app.post("/api/students/{student_id}/move-group")
    def move_student_group_v2(student_id: int,
                              payload: schemas.StudentGroupMove,
                              force: bool = False,
                              db: Session = Depends(get_db),
                              user=Depends(require_role(*roles.FREEZE_ROLES))):
        # FILIAL CHEGARASI (2026-09-06 auditi)
        s = M._get_student_in_scope(db, student_id, user)
        if payload.group_id:
            g = db.query(models.Group).get(payload.group_id)
            if g and s.branch_id and g.branch_id and \
                    g.branch_id != s.branch_id:
                raise HTTPException(
                    400, "Bu guruh boshqa filialda. Filialni almashtirish "
                         "uchun \"Boshqa filialga o'tkazish\" amalidan "
                         "foydalaning")
        return _cur_move_group(student_id=student_id, payload=payload,
                               force=force, db=db, user=user)


@app.post("/api/students/{student_id}/move-branch")
def move_student_branch(student_id: int, payload: dict,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FREEZE_ROLES))):
    """O'quvchini boshqa filialga o'tkazadi.

    Guruh tanlansa — o'sha filialdagi guruhga qo'shiladi; tanlanmasa
    guruhsiz o'tadi va yangi filial administratori guruh tanlaydi.
    Ikkala holatda ham u yerdagi administratorga vazifa tushadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    bid = payload.get("branch_id")
    if not bid:
        raise HTTPException(400, "Filial tanlanmadi")
    br = db.query(models.Branch).get(int(bid))
    if not br:
        raise HTTPException(404, "Filial topilmadi")
    if s.branch_id == br.id:
        raise HTTPException(400, "O'quvchi allaqachon shu filialda")

    g = None
    gid = payload.get("group_id")
    if gid:
        g = db.query(models.Group).get(int(gid))
        if not g:
            raise HTTPException(404, "Guruh topilmadi")
        if g.branch_id != br.id:
            raise HTTPException(400, "Bu guruh tanlangan filialda emas")
        M._raise_if_blocked(M._check_enrolment(db, s, g), force=force)

    old_branch = s.branch.name if s.branch else "—"
    old_group = s.group.name if s.group else None
    note = str(payload.get("note") or "").strip()

    s.branch_id = br.id
    s.group_id = g.id if g else None
    if g and not s.level:
        s.subject = s.subject or g.subject
        s.level = g.level

    admin = _branch_admin(db, br.id)
    bal = M.student_balance(db, s.id)
    lines = [f"O'quvchi: {s.full_name}",
             f"Qayerdan: {old_branch}"
             + (f" · {old_group}" if old_group else ""),
             f"Guruh: {g.name if g else 'hali tanlanmagan — guruh tanlang'}",
             f"Balans: {bal:,.0f} so'm".replace(",", " ")]
    if note:
        lines.append(f"Izoh: {note}")
    lines.append("")
    lines.append("Kerak: o'quvchini kutib oling, guruhini va dars "
                 "jadvalini tasdiqlang, ota-onasiga xabar bering.")

    task = models.Task(
        title=f"Yangi o'quvchi keldi: {s.full_name} ({old_branch}dan)",
        description="\n".join(lines),
        assignee_id=admin.id if admin else None,
        branch_id=br.id,
        deadline=M.roles.local_today() + M.timedelta(days=2),
        priority="high", source="manual",
        created_by=user.full_name)
    db.add(task)
    db.flush()
    try:
        M._ensure_public_id(db, "task", task)
    except Exception:
        pass

    audit.log(db, user, entity="student", action="group_move",
              entity_id=s.id, entity_label=s.full_name, field="branch",
              old_value=old_branch, new_value=br.name, branch_id=br.id,
              note=note or None)
    db.commit()
    return {"ok": True, "branch_id": br.id, "branch": br.name,
            "group_id": g.id if g else None,
            "group": g.name if g else None,
            "task_for": admin.full_name if admin else None}


# =====================================================================
#  GURUH BOSQICHI: "Step 2 · Unit 7"
#  Administrator guruhga kirganda guruh qayerga yetganini darrov ko'radi.
#  Manba — IMTIHONLAR: natijasi kiritilgan eng oxirgi unit imtihoni.
#  Hech kim qo'lda hech nima kiritmaydi, shuning uchun bu ma'lumot
#  hech qachon eskirmaydi.
# =====================================================================
_UNIT_TOTAL = 12


@app.get("/api/groups/{group_id}/progress")
def group_progress(group_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ATTENDANCE_VIEW))):
    g = _get_group_in_scope(db, group_id, user)

    rows = (db.query(models.Exam)
            .join(models.ExamResult,
                  models.ExamResult.exam_id == models.Exam.id)
            .filter(models.Exam.group_id == group_id,
                    models.Exam.kind == "unit",
                    models.Exam.unit_no.isnot(None),
                    models.ExamResult.score.isnot(None))
            .distinct().all())

    done = sorted({int(e.unit_no) for e in rows if e.unit_no})
    last = None
    for e in rows:
        if last is None or (int(e.unit_no or 0), e.date) > \
                (int(last.unit_no or 0), last.date):
            last = e

    exam_out = None
    if last is not None:
        res = (db.query(models.ExamResult)
               .filter(models.ExamResult.exam_id == last.id,
                       models.ExamResult.score.isnot(None)).all())
        # Retake/yangi kelganlar guruh o'rtachasiga kirmaydi
        pcts = [r.percent for r in res if r.percent is not None
                and (r.counted is None or r.counted != 0)]
        exam_out = {
            "id": last.id,
            "date": last.date.isoformat() if last.date else None,
            "unit_no": int(last.unit_no or 0),
            "title": last.title,
            "students": len(res),
            "avg_percent": (round(sum(pcts) / len(pcts), 1)
                            if pcts else None),
        }

    unit = int(last.unit_no or 0) if last is not None else 0
    lvl = g.level or ""
    return {
        "group_id": g.id,
        "subject": g.subject,
        "level": lvl or None,
        "level_label": roles.LEVEL_LABELS.get(lvl) or (lvl or None),
        "unit": unit,
        "unit_total": _UNIT_TOTAL,
        "next_unit": (unit + 1) if 0 < unit < _UNIT_TOTAL else
                     (1 if unit == 0 else None),
        "done_units": done,
        "percent": round(unit * 100 / _UNIT_TOTAL) if unit else 0,
        "last_exam": exam_out,
    }


# =====================================================================
#  SUPPORT YO'QLAMASI — USTOZNIKIDAN BUTUNLAY ALOHIDA
#
#  Muammo: support ham, ustoz ham BITTA "attendances" jadvaliga
#  yozardi. Support belgi qo'yganda ustozning belgisi ustiga yozilib
#  ketardi — ustoz oyligi ham shundan chiqadi, ya'ni bu pul xatosi edi.
#
#  Yechim: supportning o'z jadvali (support_attendance) va o'z kunlari.
#  Support darsi asosiy dars kuni emas — biriktirishda belgilangan
#  kun/vaqtda o'tadi, shuning uchun kunlar SupportAssignment'dan
#  quriladi. Bu jadvalga hech qanday pul hisob-kitobi bog'lanmagan:
#  ustoz oyligiga ham, o'quvchi hisobiga ham ta'sir qilmaydi.
# =====================================================================
from fastapi import Body  # noqa: E402
from pydantic import BaseModel as _BM  # noqa: E402

if getattr(models, "SupportAttendance", None) is None:
    class SupportAttendance(_Base):
        """Support teacherning o'z seansidagi yo'qlamasi."""

        __tablename__ = "support_attendance"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        group_id = Column(Integer, index=True, nullable=False)
        student_id = Column(Integer, index=True, nullable=False)
        date = Column(_SaDate, nullable=False, index=True)
        # 1 = keldi, 2 = kech keldi, 0 = kelmadi
        present = Column(Integer, default=1)
        note = Column(String)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    models.SupportAttendance = SupportAttendance
    ensure_tables([SupportAttendance.__table__])

_SUPATT = models.SupportAttendance

_SUP_ROLES = (roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT)
_SUP_ATT_EDIT = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT,
                               roles.ACADEMIC_HEAD, roles.HR_MANAGER]))

_WDX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
        "fri": 4, "sat": 5, "sun": 6}


class _SupMark(_BM):
    student_id: int
    present: bool = True
    late: bool = False
    remove: bool = False


class _SupBulk(_BM):
    day: date
    marks: list[_SupMark]


def _month_bounds(year: int, month: int):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Oy 1 dan 12 gacha bo'lsin")
    start = date(year, month, 1)
    end = (date(year + 1, 1, 1) if month == 12
           else date(year, month + 1, 1)) - _td(days=1)
    return start, end


def _support_plan(db: Session, group_id: int):
    """Guruhga biriktirilgan supportlar va ularning kun/vaqti."""
    rows = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.group_id == group_id).all())
    out = []
    for a in rows:
        u = db.query(models.User).get(a.user_id) if a.user_id else None
        out.append({
            "user_id": a.user_id,
            "name": u.full_name if u else None,
            "days": [d.strip() for d in (a.days or "").split(",")
                     if d.strip()],
            "start": a.start,
            "end": a.end,
        })
    return out


def _support_dates(db: Session, g, year: int, month: int,
                   only_user: int | None = None):
    start, end = _month_bounds(year, month)
    if getattr(g, "start_date", None) and g.start_date > start:
        start = g.start_date
    if getattr(g, "end_date", None) and g.end_date < end:
        end = g.end_date
    want = set()
    for p in _support_plan(db, g.id):
        if only_user and p["user_id"] != only_user:
            continue
        for d in p["days"]:
            if d in _WDX:
                want.add(_WDX[d])
    if not want or start > end:
        return []
    out, cur = [], start
    while cur <= end:
        if cur.weekday() in want:
            out.append(cur)
        cur += _td(days=1)
    return out


@app.get("/api/groups/{group_id}/support-attendance")
def support_attendance_grid(group_id: int, year: int, month: int,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.ATTENDANCE_VIEW))):
    g = _get_group_in_scope(db, group_id, user)
    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    days = _support_dates(db, g, year, month, only_user=mine)

    # =================================================================
    #  KIM JADVALDA TURADI (2026-09-10)
    # =================================================================
    #  Jahongir: "Ustoz supportlarda muzlatilgan arxiv o'quvchilaram
    #  yo'qlamada chiqib turibdi filtrlanmayabdi".
    #
    #  Ustoz yo'qlamasida (attendance_grid_v2) bu qoida allaqachon bor
    #  va ROLGA BOG'LIQ EMAS: yo'qlama — ish haqi hujjati, muzlatilgan
    #  yoki guruhdan chiqib ketgan odamga yangi belgi qo'yilmasligi
    #  kerak. Support yo'qlamasida esa filtr faqat ustoz/support
    #  rollariga qo'llanardi va "frozen"dan boshqasini umuman
    #  ushlamasdi — arxiv va ketganlar hammaga chiqib turardi.
    #
    #  Endi bu yerda ham xuddi ustoznikidek: jadvalda faqat FAOL
    #  o'quvchilar. Ma'lumot O'CHIRILMAYDI — yozuvlar bazada joyida,
    #  faqat shu jadvalda ko'rsatilmaydi.
    _SKIP = ("frozen", "archived", "left")
    students = [s for s in M._group_students(db, group_id)
                if s.status not in _SKIP]

    marks = {}
    if days:
        rows = (db.query(_SUPATT)
                .filter(_SUPATT.group_id == group_id,
                        _SUPATT.date >= days[0],
                        _SUPATT.date <= days[-1]).all())
        for r in rows:
            v = 2 if (r.present or 0) == 2 else bool(r.present)
            marks[f"{r.date.isoformat()}:{r.student_id}"] = v

    plan = _support_plan(db, group_id)
    label = " · ".join(
        f"{p['name'] or 'Support'} ({p['start']}-{p['end']})"
        for p in plan if p["start"] and p["end"]) or None

    return {
        "days": [d.isoformat() for d in days],
        "students": [{"id": s.id, "full_name": s.full_name,
                      "status": s.status} for s in students],
        "marks": marks,
        "plan": plan,
        "label": label,
        "today": roles.local_today().isoformat(),
        "can_edit": user.role in tuple(_SUP_ATT_EDIT),
        "can_past": user.role in tuple(roles.PAST_ATTENDANCE),
        "hint": (None if days else
                 "Support darsining kuni va vaqti belgilanmagan — "
                 "guruh kartasidan supportni biriktirib, kun va "
                 "vaqtini tanlang"),
    }


@app.put("/api/groups/{group_id}/support-attendance")
def save_support_attendance(group_id: int, payload: _SupBulk = Body(...),
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*_SUP_ATT_EDIT))):
    g = _get_group_in_scope(db, group_id, user)
    d = payload.day
    today = roles.local_today()
    if d > today:
        raise HTTPException(
            400, "Hali kelmagan kunga yo'qlama qo'yilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunni faqat asoschi, o'quv bo'limi "
                 "rahbari va HR menejer o'zgartira oladi")

    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    allowed = set(_support_dates(db, g, d.year, d.month, only_user=mine))
    if d not in allowed:
        raise HTTPException(
            400, "Bu kun support darsi kuni emas — biriktirishda "
                 "belgilangan kunlarga yo'qlama qo'yiladi")

    existing = {r.student_id: r for r in db.query(_SUPATT).filter(
        _SUPATT.group_id == group_id, _SUPATT.date == d).all()}
    for m in payload.marks:
        if m.remove:
            row = existing.pop(m.student_id, None)
            if row is not None:
                db.delete(row)
            continue
        val = (2 if m.late else 1) if m.present else 0
        row = existing.get(m.student_id)
        if row is not None:
            row.present = val
        else:
            row = _SUPATT(group_id=group_id, student_id=m.student_id,
                          date=d, present=val,
                          created_by=user.full_name)
            db.add(row)
            existing[m.student_id] = row
    db.commit()
    return {"ok": True, "date": d.isoformat(),
            "marked": len(existing)}


# --- Ustozning yo'qlamasi supportdan himoyalandi ---
_cur_save_att = _find_endpoint("/api/lessons/{lesson_id}/attendance", "PUT")

if _cur_save_att is not None:
    _drop_route("/api/lessons/{lesson_id}/attendance", "PUT")

    @app.put("/api/lessons/{lesson_id}/attendance")
    def save_attendance_v2(lesson_id: int, payload: schemas.AttendanceBulk,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*_TEACH_HR))):
        if user.role in _SUP_ROLES:
            raise HTTPException(
                403, "Ustozning yo'qlamasi alohida — unga tegilmaydi. "
                     "O'z yo'qlamangizni \"Support davomati\" "
                     "bo'limidan qo'ying")
        return _cur_save_att(lesson_id=lesson_id, payload=payload,
                             db=db, user=user)


# =====================================================================
#  LC UP IMPORTI: KETGAN (ARXIV) O'QUVCHILARNI HAM QO'SHIB KETSIN
#
#  Muammo: eski to'lovlar tarixida allaqachon ketib bo'lgan o'quvchilar
#  ko'p. Ular yangi tizimga umuman kiritilmagan, shuning uchun import
#  "bunday o'quvchi topilmadi" deb yuz-yuzlab qatorni tashlab ketardi.
#
#  Yechim: "create_missing" belgilansa, topilmagan odam ARXIV
#  o'quvchi sifatida ochiladi (status="archived") va to'lovi o'shanga
#  yoziladi. Ular Arxiv bo'limida ko'rinadi, faol ro'yxatga
#  aralashmaydi va hech qanday oylik/hisob-kitobga kirmaydi.
# =====================================================================
_LCUP_STU_NOTE = f"{_LCUP_TAG} arxivdan ko'chirilgan o'quvchi"

_orig_import_payments = _find_endpoint("/api/lcup/payments", "POST")
_drop_route("/api/lcup/payments", "POST")


def _lcup_new_student(db: Session, user, name: str, phone: str | None,
                      day):
    """Topilmagan odamni arxiv o'quvchi qilib ochadi."""
    s = models.Student(
        full_name=name.strip(),
        phone=(f"998{phone}" if phone and len(phone) == 9 else phone) or None,
        status="archived",
        branch_id=(None if user.role in tuple(roles.ORG_WIDE_ROLES)
                   else user.branch_id),
        enrolled_date=day,
        left_date=day,
        note=_LCUP_STU_NOTE,
    )
    db.add(s)
    db.flush()
    try:
        M._ensure_public_id(db, "student", s)
    except Exception:
        pass
    return s


@app.post("/api/lcup/payments")
def import_payments_v2(payload: dict, db: Session = Depends(get_db),
                       user=Depends(require_role(*_IMPORT_ROLES))):
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    create_missing = bool(payload.get("create_missing"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    by_name, by_phone = _student_index(db, user)
    seen = set()
    for p in (db.query(models.Payment)
              .filter(models.Payment.kind == "payment",
                      models.Payment.note.like(f"%{_LCUP_TAG}%")).all()):
        seen.add((p.student_id, p.created_at.date() if p.created_at else None,
                  round(p.amount, 2)))

    # Ko'rib chiqishda (commit=false) hech kim yaratilmaydi — shuning
    # uchun bitta odam necha marta to'lagan bo'lsa ham bir marta
    # sanaladi.
    planned = {}
    out, ok, dup, miss, made, total = [], 0, 0, 0, 0, 0.0

    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        amount = _parse_money(r.get("amount"))
        day = _parse_day(r.get("date"))
        phone = _phone_tail(r.get("phone"))

        if not name and not phone:
            continue
        if amount <= 0:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "summa yo'q yoki noto'g'ri"})
            continue
        if not day:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "sana o'qilmadi"})
            continue

        cands = list(by_name.get(_norm_name(name), []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in cands if s in ph]
            if both:
                cands = both
            elif not cands:
                cands = list(ph)

        new_one = False
        if not cands:
            if not create_missing or not name:
                miss += 1
                out.append({"row": i + 1, "name": name,
                            "date": day.isoformat(), "amount": amount,
                            "status": "not_found",
                            "reason": "bunday o'quvchi topilmadi"})
                continue
            key = _norm_name(name)
            if commit:
                s = _lcup_new_student(db, user, name, phone, day)
                by_name.setdefault(key, []).append(s)
                if phone:
                    by_phone.setdefault(phone, []).append(s)
                cands = [s]
                made += 1
                new_one = True
            else:
                if key not in planned:
                    planned[key] = True
                    made += 1
                total += amount
                ok += 1
                out.append({"row": i + 1, "name": name,
                            "date": day.isoformat(), "amount": amount,
                            "status": "will_create",
                            "reason": "arxiv o'quvchi sifatida ochiladi"})
                continue
        elif len(cands) > 1:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "ambiguous",
                        "reason": f"{len(cands)} ta bir xil ismli o'quvchi "
                                  f"bor — telefon ustunini qo'shing"})
            continue

        s = cands[0]
        key = (s.id, day, round(amount, 2))
        if key in seen:
            dup += 1
            out.append({"row": i + 1, "name": s.full_name,
                        "date": day.isoformat(), "amount": amount,
                        "status": "duplicate",
                        "reason": "bu to'lov allaqachon ko'chirilgan"})
            continue
        seen.add(key)

        method = _parse_method(r.get("method"))
        note = str(r.get("note") or "").strip()
        total += amount
        ok += 1
        out.append({"row": i + 1, "name": s.full_name, "student_id": s.id,
                    "date": day.isoformat(), "amount": amount,
                    "method": method,
                    "status": "created" if new_one else "ok"})

        if commit:
            when = _dt.combine(day, _dt.min.time())
            tail = f" · {note}" if note else ""
            db.add(models.Payment(
                student_id=s.id, amount=abs(amount), kind="payment",
                method=method, created_at=when, period=None,
                note=f"{_LCUP_TAG} eski to'lov{tail}",
                created_by=user.full_name))
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                created_at=when, period=None,
                note=f"{_LCUP_TAG} eski hisob ({day.strftime('%Y-%m')})",
                created_by=user.full_name))

    if commit and (ok or made):
        db.commit()
        audit.log(db, user, entity="payment", action="import",
                  entity_label=f"LC UP: {ok} ta eski to'lov"
                               + (f", {made} ta arxiv o'quvchi" if made
                                  else ""),
                  new_value=ok,
                  note=f"jami {total:,.0f} so'm".replace(",", " "),
                  commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "not_found": miss, "created": made, "total": round(total, 2),
            "rows": out[:500], "shown": min(len(out), 500),
            "all_rows": len(out)}


# Bekor qilishda import ochgan arxiv o'quvchilar ham ketadi — lekin
# faqat o'zidan boshqa hech qanday izi qolmaganlari.
_drop_route("/api/lcup/payments", "DELETE")


@app.delete("/api/lcup/payments")
def import_payments_undo_v2(db: Session = Depends(get_db),
                            user=Depends(require_role(roles.FOUNDER))):
    n = (db.query(models.Payment)
         .filter(models.Payment.note.like(f"%{_LCUP_TAG}%"))
         .delete(synchronize_session=False))
    db.flush()

    gone = 0
    for s in (db.query(models.Student)
              .filter(models.Student.note == _LCUP_STU_NOTE).all()):
        busy = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id).count()
                or db.query(models.Attendance)
                .filter(models.Attendance.student_id == s.id).count()
                or db.query(models.ExamResult)
                .filter(models.ExamResult.student_id == s.id).count())
        if busy:
            continue
        db.delete(s)
        gone += 1

    db.commit()
    audit.log(db, user, entity="payment", action="delete",
              entity_label="LC UP importi bekor qilindi",
              old_value=n,
              note=(f"{gone} ta arxiv o'quvchi ham o'chirildi"
                    if gone else None),
              commit=True)
    return {"deleted": n, "students_deleted": gone}


# =====================================================================
#  GURUHGA AVTOMAT NOM: "J/Z - Group 01/25"
#
#  Guruh ochayotgan odam nom o'ylab o'tirmasin. Qoida oddiy:
#    J/Z      — ustozning ism-familiya bosh harflari
#    Group 01 — guruh ochilgan OY (01 = yanvar)
#    /25      — yil (2025)
#  Bir ustozda shu oyda ikkinchi guruh bo'lsa oxiriga "-2" qo'shiladi.
#  Nom oddiy matn bo'lib qoladi — ustoz xohlasa o'zgartiradi, tegmasa
#  avtomat nom ketaveradi.
# =====================================================================
def _initials(full_name: str) -> str:
    parts = [p for p in (full_name or "").replace(".", " ").split() if p]
    letters = [p[0].upper() for p in parts[:2]]
    return "/".join(letters) if letters else "XX"


def _auto_group_name(db: Session, teacher_id=None, when=None) -> str:
    d = when or roles.local_today()
    who = "XX"
    if teacher_id:
        t = db.query(models.Teacher).get(int(teacher_id))
        if t:
            who = _initials(t.full_name)
    base = f"{who} - Group {d.month:02d}/{d.year % 100:02d}"
    taken = {g.name for g in db.query(models.Group)
             .filter(models.Group.name.like(f"{base}%")).all()}
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


# Diqqat: /api/groups/{group_id} yo'li allaqachon ro'yxatdan o'tgan va
# "suggest-name" ni raqam deb o'qib yuborardi — shuning uchun alohida
# prefiks.
@app.get("/api/group-name/suggest")
def group_suggest_name(teacher_id: int | None = None,
                       on: date | None = None,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.GROUP_MANAGE))):
    return {"name": _auto_group_name(db, teacher_id, on)}


_cur_create_group2 = _find_endpoint("/api/groups", "POST")

if _cur_create_group2 is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v4(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE, roles.ADMINISTRATOR, roles.SALES_MANAGER))):
        # Nom bo'sh yuborilsa — o'zi qo'yiladi (frontendda ham
        # oldindan ko'rsatiladi, bu esa ikkinchi himoya).
        if not (payload.name or "").strip():
            payload.name = _auto_group_name(
                db, payload.teacher_id, payload.start_date)
        return _cur_create_group2(payload=payload, force=force,
                                  db=db, user=user)


# =====================================================================
#  SUPPORT SEANSI YO'QLAMA BILAN BIRGA — HAQIQIY SOAT BILAN
#
#  Ilgari support oyligi qo'lda kiritilgan seansdan chiqardi va amalda
#  hamma joyda 1 soat bo'lib qolardi. Aslida asosiy ustoz ko'proq
#  vazifa berganda support 1.5, 2, hatto 3 soat ishlaydi.
#
#  Endi support yo'qlamani qo'yayotganda O'SHA OYNADA "qaysi vaqtdan
#  qaysi vaqtgacha" ni ham kiritadi. Shu ma'lumotdan seans yozuvi
#  avtomat yaratiladi/yangilanadi va oylik aynan shundan hisoblanadi.
#
#  Muhim: KELMAGAN o'quvchi sanalmaydi — seansdagi "o'quvchilar soni"
#  faqat kelganlardan iborat.
# =====================================================================
class _SupBulk2(_BM):
    day: date
    marks: list[_SupMark] = []
    start_time: str | None = None
    end_time: str | None = None
    # QO'LDA SOAT (2026-08-10, Jahongir): support tugash vaqtini
    # hisoblab o'tirmaydi - necha soat dars o'tganini o'zi tanlaydi
    # (1-3), tugash vaqtini server chiqaradi.
    hours: float | None = None


def _sup_teacher_for(db: Session, user, group_id: int):
    """Seans kimning nomiga yoziladi: supportning o'zi, aks holda shu
    guruhga biriktirilgan support."""
    if user.role == roles.SUPPORT_TEACHER:
        return M._teacher_of_user(db, user)
    a = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.group_id == group_id).first())
    if a and a.user_id:
        u = db.query(models.User).get(a.user_id)
        if u:
            return M._teacher_of_user(db, u)
    return None


def _sup_plan_time(db: Session, group_id: int, uid=None):
    q = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.group_id == group_id))
    if uid:
        q = q.filter(models.SupportAssignment.user_id == uid)
    a = q.first()
    return (a.start, a.end) if a else (None, None)


def _sync_support_session(db: Session, user, g, d, start, end):
    """Kunlik seansni yo'qlamaga qarab yangilaydi."""
    t = _sup_teacher_for(db, user, g.id)
    if t is None:
        return None
    present = (db.query(_SUPATT)
               .filter(_SUPATT.group_id == g.id, _SUPATT.date == d,
                       _SUPATT.present != 0).count())
    row = (db.query(models.SupportSession)
           .filter(models.SupportSession.teacher_id == t.id,
                   models.SupportSession.group_id == g.id,
                   models.SupportSession.date == d).first())

    # Hech kim kelmagan (yoki belgilar olib tashlangan) — seans yo'q
    if present <= 0:
        if row is not None:
            db.delete(row)
        return None

    if not (start and end):
        if row is not None:
            start = start or row.start_time
            end = end or row.end_time
        else:
            ps, pe = _sup_plan_time(db, g.id,
                                    user.id if user.role ==
                                    roles.SUPPORT_TEACHER else None)
            start, end = start or ps, end or pe
    if not (start and end):
        raise HTTPException(
            400, "Dars qaysi vaqtdan qaysi vaqtgacha bo'lganini "
                 "kiriting — oylik shu soatdan hisoblanadi")

    s_min, e_min = roles.hhmm_minutes(start), roles.hhmm_minutes(end)
    if s_min is None or e_min is None:
        raise HTTPException(400, "Vaqt SS:DD ko'rinishida bo'lsin, "
                                 "masalan 14:30")
    if e_min <= s_min:
        raise HTTPException(400, "Tugash vaqti boshlanishdan keyin "
                                 "bo'lishi kerak")
    minutes = e_min - s_min
    # 1-3 SOAT QOIDASI bu yo'lda ham (POST /me/support-sessions bilan
    # bir xil) - ikki eshikdan kirganda ikki xil qoida bo'lmasin.
    if minutes < roles.SUPPORT_SESSION_MIN_HOURS * 60:
        raise HTTPException(
            400, f"Seans kamida {roles.SUPPORT_SESSION_MIN_HOURS} "
                 f"soat bo'ladi — soatni tekshiring")
    if minutes > roles.SUPPORT_SESSION_MAX_HOURS * 60:
        raise HTTPException(
            400, f"Bitta seans {roles.SUPPORT_SESSION_MAX_HOURS} "
                 f"soatdan oshmaydi — vaqtni tekshiring")

    present = min(present, roles.SUPPORT_SESSION_MAX_STUDENTS)
    if row is None:
        row = models.SupportSession(
            teacher_id=t.id, group_id=g.id, branch_id=g.branch_id,
            date=d, start_time=start, end_time=end, minutes=minutes,
            students_count=present, note="Yo'qlamadan avtomat",
            created_by=user.id)
        db.add(row)
    else:
        row.start_time, row.end_time = start, end
        row.minutes, row.students_count = minutes, present
    return row


_drop_route("/api/groups/{group_id}/support-attendance", "PUT")


@app.put("/api/groups/{group_id}/support-attendance")
def save_support_attendance_v2(group_id: int,
                               payload: _SupBulk2 = Body(...),
                               db: Session = Depends(get_db),
                               user=Depends(require_role(*_SUP_ATT_EDIT))):
    g = _get_group_in_scope(db, group_id, user)
    d = payload.day
    today = roles.local_today()
    if d > today:
        raise HTTPException(
            400, "Hali kelmagan kunga yo'qlama qo'yilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunni faqat asoschi, o'quv bo'limi "
                 "rahbari va HR menejer o'zgartira oladi")

    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    allowed = set(_support_dates(db, g, d.year, d.month, only_user=mine))
    if d not in allowed:
        raise HTTPException(
            400, "Bu kun support darsi kuni emas — biriktirishda "
                 "belgilangan kunlarga yo'qlama qo'yiladi")

    existing = {r.student_id: r for r in db.query(_SUPATT).filter(
        _SUPATT.group_id == group_id, _SUPATT.date == d).all()}
    for m in payload.marks:
        if m.remove:
            row = existing.pop(m.student_id, None)
            if row is not None:
                db.delete(row)
            continue
        val = (2 if m.late else 1) if m.present else 0
        row = existing.get(m.student_id)
        if row is not None:
            row.present = val
        else:
            row = _SUPATT(group_id=group_id, student_id=m.student_id,
                          date=d, present=val,
                          created_by=user.full_name)
            db.add(row)
            existing[m.student_id] = row
    db.flush()

    start = (payload.start_time or "").strip() or None
    end = (payload.end_time or "").strip() or None
    if payload.hours is not None:
        # Soat berildi - tugash vaqtini o'zimiz chiqaramiz. Chegara
        # tekshiruvi baribir _sync_support_session ichida ham bor,
        # bu yerdagisi aniqroq xato matni uchun.
        try:
            _hrs = float(payload.hours)
        except (TypeError, ValueError):
            raise HTTPException(400, "Soatni to'g'ri tanlang")
        if not (roles.SUPPORT_SESSION_MIN_HOURS <= _hrs
                <= roles.SUPPORT_SESSION_MAX_HOURS):
            raise HTTPException(
                400, f"Seans {roles.SUPPORT_SESSION_MIN_HOURS}-"
                     f"{roles.SUPPORT_SESSION_MAX_HOURS} soat "
                     f"oralig'ida bo'ladi")
        if not start:
            _ps, _pe = _sup_plan_time(
                db, group_id,
                user.id if user.role == roles.SUPPORT_TEACHER else None)
            start = _ps
        if not start:
            raise HTTPException(
                400, "Dars soat nechada boshlanganini kiriting")
        _sm = roles.hhmm_minutes(start)
        if _sm is None:
            raise HTTPException(400, "Vaqt SS:DD ko'rinishida bo'lsin, "
                                     "masalan 14:30")
        _em = _sm + int(round(_hrs * 60))
        end = f"{(_em // 60) % 24:02d}:{_em % 60:02d}"

    ses = _sync_support_session(db, user, g, d, start, end)
    db.commit()
    return {
        "ok": True, "date": d.isoformat(), "marked": len(existing),
        "session": ({"start": ses.start_time, "end": ses.end_time,
                     "minutes": ses.minutes,
                     "hours": round(ses.minutes / 60, 2),
                     "students": ses.students_count}
                    if ses is not None else None),
    }


# --- Jadval: kunlik seans vaqtlari ham qaytsin ---
_orig_sup_grid = _find_endpoint("/api/groups/{group_id}/support-attendance",
                                "GET")

if _orig_sup_grid is not None:
    _drop_route("/api/groups/{group_id}/support-attendance", "GET")

    @app.get("/api/groups/{group_id}/support-attendance")
    def support_attendance_grid_v2(group_id: int, year: int, month: int,
                                   db: Session = Depends(get_db),
                                   user=Depends(require_role(
                                       *roles.ATTENDANCE_VIEW))):
        data = _orig_sup_grid(group_id=group_id, year=year, month=month,
                              db=db, user=user)
        days = data.get("days") or []
        ses = {}
        if days:
            q = (db.query(models.SupportSession)
                 .filter(models.SupportSession.group_id == group_id,
                         models.SupportSession.date >= date.fromisoformat(
                             days[0]),
                         models.SupportSession.date <= date.fromisoformat(
                             days[-1])))
            if user.role == roles.SUPPORT_TEACHER:
                t = M._teacher_of_user(db, user)
                if t:
                    q = q.filter(models.SupportSession.teacher_id == t.id)
            for r in q.all():
                ses[r.date.isoformat()] = {
                    "start": r.start_time, "end": r.end_time,
                    "minutes": r.minutes,
                    "hours": round((r.minutes or 0) / 60, 2),
                    "students": r.students_count,
                }
        ps, pe = _sup_plan_time(
            db, group_id,
            user.id if user.role == roles.SUPPORT_TEACHER else None)
        data["sessions"] = ses
        data["default_start"] = ps
        data["default_end"] = pe
        data["hours_total"] = round(
            sum(v["minutes"] or 0 for v in ses.values()) / 60, 2)
        data["students_total"] = sum(v["students"] or 0
                                     for v in ses.values())
        return data


# =====================================================================
#  ARXIV O'QUVCHILARNI EXCEL'DAN QO'SHISH
#
#  LC UP'dagi ketgan o'quvchilar ro'yxati bir marta ko'chiriladi.
#  Ular ARXIV holatida ochiladi: faol ro'yxatga, oylikka, hisob-kitobga
#  va yo'qlamaga umuman aralashmaydi — faqat tarix va eski to'lovlar
#  bog'lanadigan karta bo'lib turadi.
#
#  Bir tugma bilan bekor qilinadi (asoschi) — import ochgan, boshqa
#  hech qanday izi yo'q kartalar o'chadi.
# =====================================================================
_ARCH_TAG = "[ARXIV IMPORT]"
_ARCH_IMPORT_ROLES = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.ACCOUNTANT, roles.FINANCE_DIRECTOR]))


def _parse_date_any(v):
    """01.02.2024 / 2024-02-01 / 1.2.24 — hammasini o'qiydi."""
    s = str(v or "").strip()
    if not s:
        return None
    s = s.split(" ")[0].replace("/", ".").replace("-", ".")
    parts = [p for p in s.split(".") if p]
    if len(parts) != 3:
        return None
    try:
        a, b, c = (int(p) for p in parts)
    except ValueError:
        return None
    if a > 31:                      # yil oldinda
        y, m, d = a, b, c
    else:
        d, m, y = a, b, c
    if y < 100:
        y += 2000
    try:
        return date(y, m, d)
    except ValueError:
        return None


@app.post("/api/archive/students/import")
def archive_students_import(payload: dict, db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *_ARCH_IMPORT_ROLES))):
    """Excel'dan arxiv o'quvchilar. commit=false — faqat ko'rib chiqish."""
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    branches = {}
    for b in db.query(models.Branch).all():
        branches[_norm_name(b.name)] = b
    groups = {}
    for g in db.query(models.Group).all():
        groups.setdefault(_norm_name(g.name), g)

    by_name, by_phone = _student_index(db, user)
    my_branch = (None if user.role in tuple(roles.ORG_WIDE_ROLES)
                 else user.branch_id)

    out, ok, dup, bad = [], 0, 0, 0
    planned = set()
    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        if not name:
            continue
        phone = _phone_tail(r.get("phone"))
        pphone = _phone_tail(r.get("parent_phone"))
        key = _norm_name(name)

        if len(name) < 3:
            bad += 1
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "ism juda qisqa"})
            continue

        # Allaqachon bormi — ism + telefon bo'yicha
        found = list(by_name.get(key, []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in found if s in ph]
            found = both or (found if not ph else found)
        if found or (key, phone) in planned:
            dup += 1
            st = found[0] if found else None
            out.append({
                "row": i + 1, "name": name, "status": "duplicate",
                "reason": (f"allaqachon bor ({st.status})" if st
                           else "faylda ikki marta"),
            })
            continue
        planned.add((key, phone))

        b = branches.get(_norm_name(r.get("branch")))
        g = groups.get(_norm_name(r.get("group")))
        bid = (b.id if b else None) or (g.branch_id if g else None) \
            or my_branch
        enrolled = _parse_date_any(r.get("enrolled"))
        left = _parse_date_any(r.get("left"))

        ok += 1
        out.append({
            "row": i + 1, "name": name, "status": "ok",
            "phone": phone or None,
            "branch": (b.name if b else None),
            "group": (g.name if g else None),
            "enrolled": enrolled.isoformat() if enrolled else None,
            "left": left.isoformat() if left else None,
        })

        if commit:
            note = str(r.get("note") or "").strip()
            s = models.Student(
                full_name=name,
                phone=(f"998{phone}" if phone else None),
                parent_phone=(f"998{pphone}" if pphone else None),
                status="archived",
                branch_id=bid,
                group_id=None,          # arxivda guruh bo'lmaydi
                enrolled_date=enrolled,
                left_date=left or roles.local_today(),
                note=(f"{_ARCH_TAG} {note}".strip()
                      + (f" · guruh: {g.name}" if g else "")),
            )
            db.add(s)
            db.flush()
            try:
                M._ensure_public_id(db, "student", s)
            except Exception:
                pass
            by_name.setdefault(key, []).append(s)
            if phone:
                by_phone.setdefault(phone, []).append(s)

    if commit and ok:
        db.commit()
        audit.log(db, user, entity="student", action="import",
                  entity_label=f"Arxiv: {ok} ta o'quvchi",
                  new_value=ok, commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "skipped": bad, "rows": out[:500],
            "shown": min(len(out), 500), "all_rows": len(out)}


@app.get("/api/archive/students/import")
def archive_students_import_stats(db: Session = Depends(get_db),
                                  user=Depends(require_role(
                                      *_ARCH_IMPORT_ROLES))):
    q = (db.query(models.Student)
         .filter(models.Student.note.like(f"{_ARCH_TAG}%")))
    rows = q.all()
    return {"count": len(rows),
            "can_undo": user.role == roles.FOUNDER}


@app.delete("/api/archive/students/import")
def archive_students_import_undo(db: Session = Depends(get_db),
                                 user=Depends(require_role(roles.FOUNDER))):
    """Import ochgan kartalarni qaytarib oladi — faqat izi yo'qlarini."""
    gone = kept = 0
    for s in (db.query(models.Student)
              .filter(models.Student.note.like(f"{_ARCH_TAG}%")).all()):
        busy = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id).count()
                or db.query(models.Attendance)
                .filter(models.Attendance.student_id == s.id).count()
                or db.query(models.ExamResult)
                .filter(models.ExamResult.student_id == s.id).count())
        if busy:
            kept += 1
            continue
        db.delete(s)
        gone += 1
    db.commit()
    audit.log(db, user, entity="student", action="delete",
              entity_label="Arxiv importi bekor qilindi",
              old_value=gone,
              note=(f"{kept} tasida to'lov/yo'qlama bor — saqlab qolindi"
                    if kept else None),
              commit=True)
    return {"deleted": gone, "kept": kept}


# =====================================================================
#  EXAMINER VA SUPPORT DARAJALARI: Volontyor -> Junior -> Middle ->
#  Senior
#
#  Volontyorga OYLIK BERILMAYDI — u tajriba to'plash bosqichi.
#  Qolgan darajalarda hisoblangan oylik koeffitsiyentga ko'paytiriladi.
#  Koeffitsiyentlar bazadan o'qiladi, asoschi istagan payt o'zgartiradi.
# =====================================================================
_GRADE_SEED = [
    ("volunteer", "Volontyor", 0.00, 1),
    ("junior", "Junior", 1.00, 2),
    ("middle", "Middle", 1.15, 3),
    ("senior", "Senior", 1.30, 4),
]
_GRADED_ROLES = (roles.EXAMINER, roles.HEAD_EXAMINER,
                 roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT)
_GRADE_SET = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))

if getattr(models, "StaffGrade", None) is None:
    class StaffGrade(_Base):
        """Xodimning darajasi (examiner / support)."""

        __tablename__ = "staff_grades"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, unique=True, nullable=False)
        grade = Column(String, default="volunteer")
        since = Column(_SaDate, default=date.today)
        note = Column(String)
        updated_by = Column(String)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    class StaffGradeRate(_Base):
        """Daraja koeffitsiyenti. Volontyor = 0 (oylik yo'q)."""

        __tablename__ = "staff_grade_rates"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        key = Column(String, unique=True, index=True, nullable=False)
        label = Column(String, nullable=False)
        coef = Column(Float, default=1.0)
        order_no = Column(Integer, default=0)

    models.StaffGrade = StaffGrade
    models.StaffGradeRate = StaffGradeRate
    ensure_tables([StaffGrade.__table__, StaffGradeRate.__table__])

_SG = models.StaffGrade
_SGR = models.StaffGradeRate


def _grade_rates(db: Session) -> dict:
    rows = db.query(_SGR).all()
    if not rows:
        try:
            for k, lbl, coef, n in _GRADE_SEED:
                db.add(_SGR(key=k, label=lbl, coef=coef, order_no=n))
            db.commit()
            rows = db.query(_SGR).all()
        except Exception:
            db.rollback()
            rows = []
    out = {r.key: {"key": r.key, "label": r.label,
                   "coef": float(r.coef or 0), "order_no": r.order_no}
           for r in rows}
    for k, lbl, coef, n in _GRADE_SEED:
        out.setdefault(k, {"key": k, "label": lbl, "coef": coef,
                           "order_no": n})
    return out


def _grade_of(db: Session, user_id: int) -> str:
    r = db.query(_SG).filter(_SG.user_id == user_id).first()
    return (r.grade if r and r.grade else "volunteer")


def _apply_grade(db: Session, rows: list, key: str = "user_id") -> list:
    """Ro'yxatdagi har bir xodimga darajani va koeffitsiyentni qo'llaydi."""
    rates = _grade_rates(db)
    for r in rows:
        uid = r.get(key)
        g = _grade_of(db, uid) if uid else "volunteer"
        info = rates.get(g) or rates["volunteer"]
        coef = float(info["coef"])
        base = float(r.get("salary") or 0)
        r["grade"] = g
        r["grade_label"] = info["label"]
        r["grade_coef"] = coef
        r["salary_base"] = round(base, 0)
        r["salary"] = round(base * coef, 0)
        # Qoldiq oylikdan keyin qayta hisoblanadi — aks holda
        # volontyorga 0 so'm oylikda ham "qoldiq" ko'rinib turardi.
        if "paid" in r:
            r["left"] = round(r["salary"] - float(r.get("paid") or 0), 0)
        if coef == 0:
            r["grade_note"] = "Volontyor — oylik berilmaydi"
    return rows


@app.get("/api/staff-grades")
def staff_grades_list(branch_id: int | None = None,
                      only: str | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYROLL_VIEW))):
    rates = _grade_rates(db)
    order = sorted(rates.values(), key=lambda x: x["order_no"])
    # only=examiner — HR "Examinerlar" bo'limi uchun (2026-10-05)
    graded = _GRADED_ROLES
    if only == "examiner":
        graded = (roles.EXAMINER, roles.HEAD_EXAMINER)
    elif only == "support":
        graded = (roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT)
    # Qo'shimcha lavozim ham (2026-10-07: Mahbuba, Jasmina holati)
    us = (db.query(models.User)
          .filter(_C._any_role_cond(graded),
                  models.User.is_active == 1)
          .order_by(models.User.full_name).all())
    us = [u for u in us if user.role in tuple(roles.ORG_WIDE_ROLES)
          or not user.branch_id or u.branch_id == user.branch_id]
    # Filial tanlangan bo'lsa - faqat shu filial xodimlari (2026-08-12)
    if branch_id:
        _extra_b = {ub.user_id for ub in db.query(models.UserBranch)
                    .filter(models.UserBranch.branch_id == branch_id).all()}
        us = [u for u in us
              if u.branch_id == branch_id or u.id in _extra_b]
    rows = []
    for u in us:
        r = db.query(_SG).filter(_SG.user_id == u.id).first()
        g = (r.grade if r and r.grade else "volunteer")
        _lbl = roles.UZ_LABELS.get(u.role, u.role)
        if u.role not in graded:
            _xr = next((r.role for r in db.query(models.UserRole)
                        .filter(models.UserRole.user_id == u.id).all()
                        if r.role in graded), None)
            if _xr:
                _lbl = f"{_lbl} + {roles.UZ_LABELS.get(_xr, _xr)}"
        rows.append({
            "user_id": u.id, "name": u.full_name,
            "role": _lbl,
            "branch": u.branch.name if u.branch else None,
            "phone": u.phone,
            "updated_by": r.updated_by if r else None,
            "grade": g,
            "grade_label": (rates.get(g) or {}).get("label", g),
            "coef": (rates.get(g) or {}).get("coef", 0),
            "since": r.since.isoformat() if r and r.since else None,
            "note": r.note if r else None,
        })
    return {"grades": order, "rows": rows,
            "can_edit": user.role in tuple(_GRADE_SET),
            "can_edit_rates": user.role == roles.FOUNDER,
            "hint": ("Volontyorga oylik berilmaydi. Junior, Middle va "
                     "Senior darajalarida hisoblangan oylik "
                     "koeffitsiyentga ko'paytiriladi.")}


@app.put("/api/staff-grades/{target_id}")
def staff_grade_set(target_id: int, payload: dict = Body(...),
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*_GRADE_SET))):
    g = str(payload.get("grade") or "").strip()
    rates = _grade_rates(db)
    if g not in rates:
        raise HTTPException(400, "Noto'g'ri daraja")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if not _C._has_any_role(db, u, _GRADED_ROLES):
        raise HTTPException(
            400, "Daraja faqat examiner va support teacherga qo'yiladi")
    row = db.query(_SG).filter(_SG.user_id == u.id).first()
    old = row.grade if row else None
    if row is None:
        row = _SG(user_id=u.id)
        db.add(row)
    row.grade = g
    row.since = roles.local_today()
    row.note = payload.get("note")
    row.updated_by = user.full_name
    db.commit()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field="Daraja",
              old_value=old, new_value=rates[g]["label"], commit=True)
    return {"ok": True, "grade": g, "label": rates[g]["label"],
            "coef": rates[g]["coef"]}


@app.put("/api/staff-grades")
def staff_grade_rates_set(payload: dict = Body(...),
                          db: Session = Depends(get_db),
                          user=Depends(require_role(roles.FOUNDER))):
    _grade_rates(db)
    _changed = []  # (row, old_coef) - keyin, commit'dan OLDIN yozib olamiz
    for it in (payload.get("rates") or []):
        k = str(it.get("key") or "")
        row = db.query(_SGR).filter(_SGR.key == k).first()
        if row is None:
            continue
        try:
            c = float(it.get("coef"))
        except (TypeError, ValueError):
            continue
        if c < 0 or c > 5:
            raise HTTPException(400, "Koeffitsiyent 0 dan 5 gacha bo'lsin")
        if c != row.coef:
            _changed.append((row, row.coef))
            row.coef = c
    db.commit()
    # Bu BARCHA xodimlarning oyligini hisoblash formulasiga ta'sir
    # qiladigan global sozlama - FOUNDER'dan boshqa hech kim
    # o'zgartira olmaydi, shuning uchun HAR bir o'zgargan (haqiqatda
    # farq qilgan, no-op emas) koeffitsiyent alohida qayd etiladi.
    for row, old_coef in _changed:
        audit.log(db, user, entity="staff_grade_rate", action="update",
                  entity_id=row.id, entity_label=row.label,
                  field="Koeffitsiyent", old_value=old_coef,
                  new_value=row.coef)
    if _changed:
        db.commit()
    return {"ok": True, "grades": sorted(_grade_rates(db).values(),
                                         key=lambda x: x["order_no"])}


# --- Oylik ro'yxatlariga daraja qo'llanadi ---
_cur_ex_sal = _find_endpoint("/api/examiners/salary", "GET")
_cur_su_sal = _find_endpoint("/api/support/salary", "GET")

if _cur_ex_sal is not None:
    _drop_route("/api/examiners/salary", "GET")

    @app.get("/api/examiners/salary")
    def examiner_salary_v3(year: int | None = None, month: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *list(dict.fromkeys(
                                   list(roles.EXAMINER_SALARY_VIEW)
                                   + _PAYROLL_VIEW))))):
        data = _cur_ex_sal(year=year, month=month, db=db, user=user)
        rows = _apply_grade(db, data.get("rows") or [], "user_id")
        data["rows"] = rows
        data["total"] = round(sum(r["salary"] for r in rows), 0)
        return data

if _cur_su_sal is not None:
    _drop_route("/api/support/salary", "GET")

    @app.get("/api/support/salary")
    def support_salary_v3(year: int | None = None, month: int | None = None,
                          branch_id: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *list(dict.fromkeys(
                                  list(roles.SALARY_VIEW_ALL)
                                  + [roles.ACADEMIC_HEAD]
                                  + _PAYROLL_VIEW))))):
        data = _cur_su_sal(year=year, month=month, db=db, user=user)
        rows = _apply_grade(db, data.get("rows") or [], "user_id")
        rows = _rows_in_branch(db, rows, branch_id)
        data["rows"] = rows
        data["total"] = round(sum(r["salary"] for r in rows), 0)
        return data


# Ustozlar ro'yxatidagi support oyligi ham darajaga bo'ysunadi
# (2026-09-23, Jahongir: volontyorga oylik hisoblanmasin). Bu yerda
# qatorlarda faqat teacher_id bor - avval user_id topiladi.
_cur_su_list = _find_endpoint("/api/support-teachers/salaries", "GET")

if _cur_su_list is not None:
    _drop_route("/api/support-teachers/salaries", "GET")

    @app.get("/api/support-teachers/salaries")
    def support_teacher_salaries_v2(year: int | None = None,
                                    month: int | None = None,
                                    db: Session = Depends(get_db),
                                    user=Depends(require_role(
                                        *roles.FULL_ACCESS,
                                        roles.ACADEMIC_HEAD,
                                        roles.HEAD_SUPPORT,
                                        roles.HR_MANAGER,
                                        roles.FINANCE_DIRECTOR))):
        data = _cur_su_list(year=year, month=month, db=db, user=user)
        rows = data.get("rows") or []
        for r in rows:
            t = db.query(models.Teacher).get(r.get("teacher_id"))
            r["user_id"] = t.user_id if t else None
        data["rows"] = _apply_grade(db, rows, "user_id")
        return data


# =====================================================================
#  HR KUTUBXONASI (onboarding)
#
#  Yangi xodim ishga kirganda ko'rishi shart bo'lgan video, kitob va
#  fayllar bir joyda turadi. Har bir xodim uchun: nechi foiz ko'rgani
#  va HR "topshirdi" deb belgilagani yoziladi. Daraja ko'tarishda shu
#  ro'yxat mezonlardan biri bo'ladi.
# =====================================================================
_LIB_KINDS = [("video", "Video"), ("book", "Kitob"),
              ("file", "Fayl"), ("link", "Havola")]
_LIB_KIND_LABELS = dict(_LIB_KINDS)
_LIB_MANAGE = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))

if getattr(models, "LibraryItem", None) is None:
    class LibraryItem(_Base):
        """Kutubxona yozuvi: video, kitob, fayl yoki havola."""

        __tablename__ = "library_items"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, nullable=False)
        kind = Column(String, default="video")
        url = Column(String)
        attachment_id = Column(Integer)
        minutes = Column(Integer, default=0)
        description = Column(String)
        # Kimlarga tegishli: rollar ro'yxati. Bo'sh = hammaga.
        target_roles = Column(String)
        required = Column(Integer, default=1)
        order_no = Column(Integer, default=0)
        active = Column(Integer, default=1)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    class LibraryProgress(_Base):
        """Kim nechi foiz ko'rgani va topshirgani."""

        __tablename__ = "library_progress"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        item_id = Column(Integer, index=True, nullable=False)
        user_id = Column(Integer, index=True, nullable=False)
        percent = Column(Integer, default=0)
        passed = Column(Integer, default=0)
        passed_at = Column(_SaDate)
        passed_by = Column(String)
        note = Column(String)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    models.LibraryItem = LibraryItem
    models.LibraryProgress = LibraryProgress
    ensure_tables([LibraryItem.__table__, LibraryProgress.__table__])

_LI = models.LibraryItem
_LP = models.LibraryProgress


def _lib_for_role(it, role: str) -> bool:
    t = [x.strip() for x in (it.target_roles or "").split(",") if x.strip()]
    return (not t) or (role in t)


def _lib_out(it, prog=None) -> dict:
    return {
        "id": it.id, "title": it.title, "kind": it.kind,
        "kind_label": _LIB_KIND_LABELS.get(it.kind, it.kind),
        "url": it.url, "attachment_id": it.attachment_id,
        "minutes": it.minutes or 0, "description": it.description,
        "target_roles": [x for x in (it.target_roles or "").split(",") if x],
        "required": bool(it.required), "order_no": it.order_no or 0,
        "active": bool(it.active),
        "percent": (prog.percent or 0) if prog else 0,
        "passed": bool(prog.passed) if prog else False,
        "passed_at": (prog.passed_at.isoformat()
                      if prog and prog.passed_at else None),
        "note": prog.note if prog else None,
    }


@app.get("/api/library")
def library_list(db: Session = Depends(get_db),
                 user=Depends(M.get_current_user)):
    """O'z ro'yxatim + (HR uchun) har bir yozuv bo'yicha umumiy holat."""
    manage = user.role in tuple(_LIB_MANAGE)
    q = db.query(_LI).order_by(_LI.order_no, _LI.id)
    items = [it for it in q.all() if manage or (
        it.active and _lib_for_role(it, user.role))]
    mine = {p.item_id: p for p in db.query(_LP)
            .filter(_LP.user_id == user.id).all()}

    out = []
    for it in items:
        row = _lib_out(it, mine.get(it.id))
        if manage:
            people = db.query(_LP).filter(_LP.item_id == it.id).all()
            row["watchers"] = len(people)
            row["done"] = len([p for p in people if p.passed])
            row["avg_percent"] = (
                round(sum(p.percent or 0 for p in people) / len(people))
                if people else 0)
        out.append(row)

    total = len([r for r in out if r["required"]])
    done = len([r for r in out if r["required"] and r["passed"]])
    return {
        "items": out, "kinds": [{"key": k, "label": l}
                                for k, l in _LIB_KINDS],
        "can_manage": manage,
        "my_total": total, "my_done": done,
        "my_percent": round(done * 100 / total) if total else 0,
        "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                  for r in roles.STAFF_ROLES],
    }


@app.post("/api/library")
def library_add(payload: dict = Body(...), db: Session = Depends(get_db),
                user=Depends(require_role(*_LIB_MANAGE))):
    title = str(payload.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Nomini kiriting")
    kind = str(payload.get("kind") or "video")
    if kind not in _LIB_KIND_LABELS:
        raise HTTPException(400, "Noto'g'ri tur")
    url = str(payload.get("url") or "").strip() or None
    aid = payload.get("attachment_id")
    # Qog'oz kitobning havolasi bo'lmasligi mumkin (2026-09-26, HR
    # checklistdan qo'shish): kitob uchun havola ixtiyoriy.
    if not url and not aid and kind != "book":
        raise HTTPException(
            400, "Havola qo'ying yoki fayl yuklang — bittasi bo'lishi kerak")
    it = _LI(
        title=title, kind=kind, url=url,
        attachment_id=int(aid) if aid else None,
        minutes=int(payload.get("minutes") or 0),
        description=str(payload.get("description") or "").strip() or None,
        target_roles=",".join(payload.get("target_roles") or []) or None,
        required=1 if payload.get("required", True) else 0,
        order_no=int(payload.get("order_no") or 0),
        active=1, created_by=user.full_name)
    db.add(it)
    db.commit()
    db.refresh(it)
    audit.log(db, user, entity="user", action="create",
              entity_label=f"Kutubxona: {title}", commit=True)
    return _lib_out(it)


@app.post("/api/library/import/archive")
def library_archive_import(payload: dict = Body(...), db: Session = Depends(get_db),
                           user=Depends(require_role(*_LIB_MANAGE))):
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip() or len(source) > 200:
        raise HTTPException(400, "Import manbasini kiriting")
    marker = "Manba: " + source.strip() + "."
    items = [it for it in db.query(_LI).filter(_LI.kind == "book", _LI.active == 1).all()
             if (it.description or "").endswith(marker)]
    for it in items:
        it.active = 0
    audit.log(db, user, entity="user", action="update",
              entity_label="Kutubxona: import yashirildi",
              note=f"{source}: {len(items)} ta kitob. Yozuvlar saqlangan.", commit=False)
    db.commit()
    return {"archived": len(items)}


@app.post("/api/library/import")
def library_import(payload: dict = Body(...), db: Session = Depends(get_db),
                   user=Depends(require_role(*_LIB_MANAGE))):
    from library_import import import_books
    result = import_books(db, _LI, payload.get("items"), user.full_name)
    audit.log(db, user, entity="user", action="create",
              entity_label="Kutubxona: kitoblar importi",
              note=f"{result['added']} ta qo'shildi, {result['skipped']} ta mavjud",
              commit=False)
    db.commit()
    return result


@app.put("/api/library/{item_id}")
def library_edit(item_id: int, payload: dict = Body(...),
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    for f in ("title", "url", "description"):
        if f in payload:
            setattr(it, f, str(payload.get(f) or "").strip() or None)
    if payload.get("kind") in _LIB_KIND_LABELS:
        it.kind = payload["kind"]
    if "minutes" in payload:
        it.minutes = int(payload.get("minutes") or 0)
    if "order_no" in payload:
        it.order_no = int(payload.get("order_no") or 0)
    if "target_roles" in payload:
        it.target_roles = ",".join(payload.get("target_roles") or []) or None
    if "required" in payload:
        it.required = 1 if payload.get("required") else 0
    if "active" in payload:
        it.active = 1 if payload.get("active") else 0
    if not it.title:
        raise HTTPException(400, "Nomini kiriting")
    db.commit()
    return _lib_out(it)


@app.delete("/api/library/{item_id}")
def library_delete(item_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    db.query(_LP).filter(_LP.item_id == item_id).delete(
        synchronize_session=False)
    name = it.title
    db.delete(it)
    db.commit()
    audit.log(db, user, entity="user", action="delete",
              entity_label=f"Kutubxona: {name}", commit=True)
    return {"ok": True}


@app.put("/api/library/{item_id}/progress")
def library_progress(item_id: int, payload: dict = Body(...),
                     db: Session = Depends(get_db),
                     user=Depends(M.get_current_user)):
    """Xodim o'zi qancha ko'rganini belgilaydi. "Topshirdi" ni HR qo'yadi."""
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    try:
        pct = int(payload.get("percent"))
    except (TypeError, ValueError):
        raise HTTPException(400, "Foizni kiriting")
    pct = max(0, min(100, pct))
    row = (db.query(_LP)
           .filter(_LP.item_id == item_id, _LP.user_id == user.id).first())
    if row is None:
        row = _LP(item_id=item_id, user_id=user.id)
        db.add(row)
    # Orqaga tushirilmaydi — ko'rilgan ko'rilgan
    row.percent = max(row.percent or 0, pct)
    db.commit()
    return _lib_out(it, row)


@app.get("/api/library/{item_id}/people")
def library_people(item_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    us = (db.query(models.User)
          .filter(models.User.is_active == 1)
          .order_by(models.User.full_name).all())
    us = [u for u in us if u.role in tuple(roles.STAFF_ROLES)
          and _lib_for_role(it, u.role)]
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        us = [u for u in us if u.branch_id == user.branch_id]
    prog = {p.user_id: p for p in db.query(_LP)
            .filter(_LP.item_id == item_id).all()}
    rows = []
    for u in us:
        p = prog.get(u.id)
        rows.append({
            "user_id": u.id, "name": u.full_name,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "percent": (p.percent or 0) if p else 0,
            "passed": bool(p and p.passed),
            "passed_at": (p.passed_at.isoformat()
                          if p and p.passed_at else None),
            "passed_by": p.passed_by if p else None,
            "note": p.note if p else None,
        })
    return {"item": _lib_out(it), "rows": rows,
            "done": len([r for r in rows if r["passed"]]),
            "total": len(rows)}


@app.put("/api/library/{item_id}/people/{target_id}")
def library_mark(item_id: int, target_id: int, payload: dict = Body(...),
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_LIB_MANAGE))):
    """HR "topshirdi" deb belgilaydi (yoki belgini olib tashlaydi)."""
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    row = (db.query(_LP)
           .filter(_LP.item_id == item_id, _LP.user_id == target_id).first())
    if row is None:
        row = _LP(item_id=item_id, user_id=target_id)
        db.add(row)
    ok = bool(payload.get("passed"))
    row.passed = 1 if ok else 0
    row.passed_at = roles.local_today() if ok else None
    row.passed_by = user.full_name if ok else None
    if ok:
        row.percent = 100
    if "percent" in payload and not ok:
        try:
            row.percent = max(0, min(100, int(payload["percent"])))
        except (TypeError, ValueError):
            pass
    if "note" in payload:
        row.note = str(payload.get("note") or "").strip() or None
    db.commit()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field=f"Kutubxona: {it.title}",
              new_value="topshirdi" if ok else "bekor qilindi",
              commit=True)
    return {"ok": True, "passed": ok, "percent": row.percent}


@app.get("/api/library/person/{target_id}")
def library_person(target_id: int, db: Session = Depends(get_db),
                   user=Depends(M.get_current_user)):
    """Bitta xodimning kutubxona holati — daraja ko'tarishda ko'riladi."""
    if target_id != user.id and user.role not in tuple(_LIB_MANAGE):
        raise HTTPException(403, "Ruxsat yo'q")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    prog = {p.item_id: p for p in db.query(_LP)
            .filter(_LP.user_id == target_id).all()}
    items = [it for it in db.query(_LI)
             .order_by(_LI.order_no, _LI.id).all()
             if it.active and _lib_for_role(it, u.role)]
    out = [_lib_out(it, prog.get(it.id)) for it in items]
    need = [r for r in out if r["required"]]
    done = [r for r in need if r["passed"]]
    return {"user_id": u.id, "name": u.full_name,
            "items": out, "total": len(need), "done": len(done),
            "percent": round(len(done) * 100 / len(need)) if need else 0}


# =====================================================================
#  ONBOARDING BOSQICHLARI — ROLGA QARAB, QO'LDA BOSHQARILADI
#
#  2026-08-20, Jahongir: "onboarding bilan majburiy kitob videolarni
#  qo'lda o'zgartiradigan qilib bering, hamma xodimga xar xilda
#  onboarding".
#
#  Ilgari bosqichlar roles.ONBOARDING_STEPS da qotib turardi - hamma
#  rolga bir xil. Endi shablon jadvali bor: HR bosqich qo'shadi,
#  nomini o'zgartiradi, qaysi rollarga tegishliligini belgilaydi.
#  Jadval BO'SH bo'lsa eski standart ro'yxat ishlaydi - hech kimning
#  checklisti yo'qolmaydi. O'chirish = faolsizlantirish (tarix
#  saqlanadi, bajarilgan belgilar OnboardingStep'da qoladi).
# =====================================================================
if getattr(models, "OnboardingTemplate", None) is None:
    class OnboardingTemplate(_Base):
        """Onboarding bosqichi shabloni."""

        __tablename__ = "onboarding_templates"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        key = Column(String, nullable=False, index=True)
        label = Column(String, nullable=False)
        # Kimlarga: rollar CSV. Bo'sh = barcha xodimlarga.
        target_roles = Column(String)
        order_no = Column(Integer, default=0)
        active = Column(Integer, default=1)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    models.OnboardingTemplate = OnboardingTemplate
    ensure_tables([OnboardingTemplate.__table__])

_OT = models.OnboardingTemplate
_ONB_MANAGE = list(dict.fromkeys(
    list(roles.HR_ACCESS) + [roles.ACADEMIC_HEAD, roles.HEAD_SUPPORT]))


def _onb_templates(db) -> list:
    try:
        rows = (db.query(_OT).order_by(_OT.order_no, _OT.id).all())
    except Exception:
        rows = []
    return rows


def _onb_steps_for_role(db, role: str) -> list:
    """Rol uchun (key, label) ro'yxati. Shablon bo'sh - eski standart."""
    rows = [t for t in _onb_templates(db) if t.active]
    if not rows:
        return list(roles.ONBOARDING_STEPS)
    out = []
    for t in rows:
        tr = [x for x in (t.target_roles or "").split(",") if x]
        if not tr or role in tr:
            out.append((t.key, t.label))
    return out


def _onboarding_rows_v2(db, user_id: int) -> list:
    """common._onboarding_rows o'rnini bosadi - ROLGA QARAB."""
    u = db.query(models.User).get(user_id)
    steps = _onb_steps_for_role(db, u.role if u else "")
    have = {r.step: r for r in db.query(models.OnboardingStep)
            .filter(models.OnboardingStep.user_id == user_id).all()}
    out = []
    for key, label in steps:
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


# Eski funksiyani hamma joyda almashtiramiz - me.py va hr.py uni
# "from common import *" orqali o'z nomiga olib bo'lgan.
import hr as _hr_mod  # noqa: E402
M._onboarding_rows = _onboarding_rows_v2
_hr_mod._onboarding_rows = _onboarding_rows_v2
try:
    import me as _me_mod  # noqa: E402
    _me_mod._onboarding_rows = _onboarding_rows_v2
except Exception:
    pass


def _slugify_key(label: str) -> str:
    import re as _re
    k = _re.sub(r"[^a-z0-9]+", "_", label.lower().replace("'", "")).strip("_")
    return (k or "step")[:40]


@app.get("/api/onboarding-steps")
def onboarding_steps_list(db: Session = Depends(get_db),
                          user=Depends(require_role(*_ONB_MANAGE))):
    rows = _onb_templates(db)
    if not rows:
        # Standartni birinchi ochilishda jadvalga ko'chiramiz -
        # shundan keyin hammasi qo'lda boshqariladi.
        for i, (k, lbl) in enumerate(roles.ONBOARDING_STEPS):
            db.add(_OT(key=k, label=lbl, order_no=i, active=1,
                       created_by="Tizim (standart)"))
        db.commit()
        rows = _onb_templates(db)
    return {
        "rows": [{
            "id": t.id, "key": t.key, "label": t.label,
            "target_roles": [x for x in (t.target_roles or "").split(",")
                             if x],
            "order_no": t.order_no or 0, "active": bool(t.active),
        } for t in rows],
        "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                  for r in roles.STAFF_ROLES],
    }


@app.post("/api/onboarding-steps")
def onboarding_steps_add(payload: dict = Body(...),
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*_ONB_MANAGE))):
    label = str(payload.get("label") or "").strip()
    if not label:
        raise HTTPException(400, "Bosqich nomini kiriting")
    key = _slugify_key(label)
    base, n = key, 2
    while db.query(_OT).filter(_OT.key == key).first():
        key = f"{base}_{n}"; n += 1
    t = _OT(key=key, label=label,
            target_roles=",".join(payload.get("target_roles") or []) or None,
            order_no=int(payload.get("order_no") or 0),
            active=1, created_by=user.full_name)
    db.add(t); db.commit(); db.refresh(t)
    audit.log(db, user, entity="user", action="create",
              entity_label=f"Onboarding bosqichi: {label}", commit=True)
    return {"ok": True, "id": t.id, "key": t.key}


@app.put("/api/onboarding-steps/{tid}")
def onboarding_steps_edit(tid: int, payload: dict = Body(...),
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*_ONB_MANAGE))):
    t = db.query(_OT).get(tid)
    if not t:
        raise HTTPException(404, "Topilmadi")
    if "label" in payload:
        lbl = str(payload.get("label") or "").strip()
        if not lbl:
            raise HTTPException(400, "Bosqich nomini kiriting")
        t.label = lbl
    if "target_roles" in payload:
        t.target_roles = ",".join(payload.get("target_roles") or []) or None
    if "order_no" in payload:
        t.order_no = int(payload.get("order_no") or 0)
    if "active" in payload:
        t.active = 1 if payload.get("active") else 0
    db.commit()
    return {"ok": True}


@app.delete("/api/onboarding-steps/{tid}")
def onboarding_steps_del(tid: int, db: Session = Depends(get_db),
                         user=Depends(require_role(*_ONB_MANAGE))):
    """O'chirish = faolsizlantirish. Bajarilgan belgilar saqlanadi."""
    t = db.query(_OT).get(tid)
    if not t:
        raise HTTPException(404, "Topilmadi")
    t.active = 0
    db.commit()
    audit.log(db, user, entity="user", action="update",
              entity_label=f"Onboarding bosqichi o'chirildi: {t.label}",
              commit=True)
    return {"ok": True}


# =====================================================================
#  SUPPORT TEACHERNING O'Z DARAJA YO'LI
#
#  Ilgari "Mening yo'lim" sahifasida supportga USTOZNING darajalari
#  (Junior teacher, 80 000 so'm har bir o'quvchidan) ko'rinardi — bu
#  xato edi, chunki supportning bosqichlari ham, talablari ham, oylik
#  hisobi ham butunlay boshqa.
#
#  Oylik hisobi O'ZGARMAYDI: seanslardan chiqadigan formula o'z holida
#  qoladi, ustiga faqat daraja koeffitsiyenti qo'llanadi. Qo'llanmadagi
#  "soatiga 2000 / 3500 / 6000 so'm" raqamlari ishlatilmaydi.
# =====================================================================
_SUP_LADDER = {
    "volunteer": {
        "groups": "—",
        "free_courses": 0,
        "cert": "CEFR B2 53+ yoki IELTS 5.5",
        "note": ("2 oylik sinov bosqichi: oylik berilmaydi va imtiyoz "
                 "yo'q. Kitob va videolarni topshirib boradi."),
    },
    "junior": {
        "groups": "2 ta guruh",
        "free_courses": 1,
        "cert": "CEFR B2 60+ yoki IELTS 6.0",
        "note": "Bitta kurs bepul.",
    },
    "middle": {
        "groups": "3–5 ta guruh",
        "free_courses": 1,
        "cert": "CEFR C1 yoki IELTS 6.5+",
        "note": "Bitta kurs bepul.",
    },
    "senior": {
        "groups": "10 tagacha guruh",
        "free_courses": 2,
        "cert": "CEFR C1 yoki IELTS 7.0+",
        "note": "Ikkita kurs bepul.",
    },
}
_SUP_VOLUNTEER_MONTHS = 2


def _months_since(d) -> float:
    if not d:
        return 0.0
    today = roles.local_today()
    return round((today - d).days / 30.44, 1)


@app.get("/api/me/support-career")
def my_support_career(db: Session = Depends(get_db),
                      user=Depends(M.get_current_user)):
    """Supportning o'z daraja yo'li. Ustoznikidan butunlay alohida."""
    if user.role not in (roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT):
        raise HTTPException(404, "Bu sahifa support teacherlar uchun")

    rates = _grade_rates(db)
    row = db.query(_SG).filter(_SG.user_id == user.id).first()
    cur = (row.grade if row and row.grade else "volunteer")

    levels = []
    for info in sorted(rates.values(), key=lambda x: x["order_no"]):
        extra = _SUP_LADDER.get(info["key"], {})
        levels.append({
            "key": info["key"],
            "label": (info["label"] + " support"
                      if info["key"] != "volunteer" else "Volontyor support"),
            "coef": info["coef"],
            "groups": extra.get("groups", "—"),
            "free_courses": extra.get("free_courses", 0),
            "cert": extra.get("cert"),
            "note": extra.get("note"),
            "paid": info["coef"] > 0,
        })

    # Hozirgi holat
    gids = [a.group_id for a in db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.user_id == user.id,
                    models.SupportAssignment.group_id.isnot(None)).all()]
    today = roles.local_today()
    t = M._teacher_of_user(db, user)
    month = {}
    if t:
        try:
            d = M._support_month(db, t.id, today.year, today.month)
            d.pop("sessions", None)
            month = d
        except Exception:
            month = {}
    base = float(month.get("salary") or 0)
    coef = float((rates.get(cur) or {}).get("coef", 0))

    # Kutubxona — daraja ko'tarishda qaraladigan mezonlardan biri
    lib_done = lib_total = 0
    try:
        prog = {p.item_id: p for p in db.query(_LP)
                .filter(_LP.user_id == user.id).all()}
        for it in db.query(_LI).all():
            if not it.active or not it.required:
                continue
            if not _lib_for_role(it, user.role):
                continue
            lib_total += 1
            p = prog.get(it.id)
            if p and p.passed:
                lib_done += 1
    except Exception:
        pass

    in_grade = _months_since(row.since if row else None)
    return {
        "kind": "support",
        "grade": cur,
        "grade_label": (rates.get(cur) or {}).get("label", cur),
        "coef": coef,
        "since": (row.since.isoformat() if row and row.since else None),
        "months_in_grade": in_grade,
        "months_total": _months_since(user.hired_date),
        "volunteer_months_needed": _SUP_VOLUNTEER_MONTHS,
        "levels": levels,
        "stats": {
            "period": month.get("period"),
            "groups": len(set(gids)),
            "hours": month.get("hours", 0),
            "students": month.get("students", 0),
            "avg_percent": month.get("avg_percent"),
            "salary_base": round(base, 0),
            "salary": round(base * coef, 0),
        },
        "library": {"done": lib_done, "total": lib_total,
                    "percent": (round(lib_done * 100 / lib_total)
                                if lib_total else 0)},
        "formula": month.get("formula"),
        "hint": ("Oylik seanslardan avtomat hisoblanadi, so'ng daraja "
                 "koeffitsiyentiga ko'paytiriladi. Volontyor bosqichida "
                 "oylik berilmaydi."),
    }


# =====================================================================
#  BAZA SXEMASI MODELDAN ORQADA QOLMASIN
#
#  create_all() faqat YO'Q JADVALNI yaratadi — mavjud jadvalga yangi
#  ustun qo'shmaydi. Shuning uchun modelga ustun qo'shilib migratsiya
#  yozilmasa, o'sha jadvalga tegadigan HAR BIR so'rov 500 beradi:
#  dashboard ham, dars jadvali ham, o'quvchilar ro'yxati ham birdan
#  qulaydi. Kod to'g'ri, baza ortda qolgan — tashqaridan qarab sababini
#  topish qiyin, chunki xato ekranda "server xatosi" bo'lib ko'rinadi.
#
#  Shu yerda ilova ishga tushganda tekshiriladi va yetishmagan ustun
#  o'zi qo'shiladi. Faqat NULL bo'la oladigan ustunlar qo'shiladi:
#  NOT NULL ustun ma'lumot bilan to'ldirilishi kerak, uni jimgina
#  qo'shib bo'lmaydi — u ro'yxatga chiqariladi va qo'lda hal qilinadi.
# =====================================================================
#  2026-08-14 (Jahongir: "Har sovuq startda ... reflection so'rovlari
#  ketadi ... shularni ham togrla"): bu tekshiruv ham HAR uyg'onishda
#  butun sxemani o'qir edi. Endi u faqat sxema stamp'i yangilanmagan
#  bo'lsa (ya'ni haqiqatan yangi migratsiya bo'lsa) ishlaydi. Kerak
#  bo'lsa qo'lda ham chaqirish mumkin: /api/system/schema-sync.
def _sync_missing_columns(force: bool = False) -> dict:
    from common import _schema_ready as _ready
    if not force and _ready():
        return {"added": [], "manual": [], "skipped": True}
    from sqlalchemy import inspect as _insp
    from sqlalchemy import text as _txt
    from sqlalchemy.schema import CreateColumn
    from database import Base as _B, engine as _eng

    try:
        insp = _insp(_eng)
        have = set(insp.get_table_names())
    except Exception:
        return {"added": [], "manual": []}

    cols_by_table = {}
    try:                                    # bitta borishda hammasi
        for key, cols in insp.get_multi_columns().items():
            name = key[1] if isinstance(key, tuple) else key
            cols_by_table[name] = {c["name"] for c in cols}
    except Exception:
        cols_by_table = {}

    added, manual = [], []
    for table in _B.metadata.sorted_tables:
        if table.name not in have:
            continue
        known = cols_by_table.get(table.name)
        if known is None:
            try:
                known = {c["name"] for c in insp.get_columns(table.name)}
            except Exception:
                continue
        for col in table.columns:
            if col.name in known or col.primary_key:
                continue
            if (not col.nullable and col.server_default is None
                    and col.default is None):
                manual.append(f"{table.name}.{col.name}")
                continue
            try:
                ddl = str(CreateColumn(col).compile(dialect=_eng.dialect))
                with _eng.begin() as cx:
                    cx.execute(_txt(
                        f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
                added.append(f"{table.name}.{col.name}")
            except Exception as exc:        # noqa: BLE001
                manual.append(f"{table.name}.{col.name} "
                              f"({exc.__class__.__name__})")
    if added:
        print("[schema] yangi ustunlar qo'shildi: " + ", ".join(added))
    if manual:
        print("[schema] qo'lda migratsiya kerak: " + ", ".join(manual))
    return {"added": added, "manual": manual}


_SCHEMA_SYNC = _sync_missing_columns()


@app.get("/api/system/schema-sync")
def system_schema_sync(force: int = 0,
                       user=Depends(require_role(*roles.FULL_ACCESS))):
    """Ishga tushganda nima qo'shilgani — xato qidirishda kerak.
    ?force=1 bilan chaqirilsa sxemani ATAYLAB qaytadan tekshiradi
    (sovuq startda bu tekshiruv endi o'tkazib yuboriladi)."""
    res = _sync_missing_columns(force=True) if force else _SCHEMA_SYNC
    return {
        "added": res.get("added", []),
        "manual": res.get("manual", []),
        "skipped": res.get("skipped", False),
        "hint": ("Bo'sh bo'lsa — baza model bilan mos. \"manual\" "
                 "ro'yxatidagi ustunlar NOT NULL, ularni qo'lda "
                 "to'ldirish kerak."),
    }


# =====================================================================
#  LC UP -> JONYOS KO'CHIRISH
#
#  1) Balans: LC UP dagi balans asosiy deb olinadi. Har o'quvchiga
#     farqni yopadigan BITTA "[LC UP] balans tenglashtirish" yozuvi
#     qo'shiladi. Qayta yuborilsa eski tenglashtirish o'chirilib,
#     yangisi yoziladi — ya'ni necha marta bosilsa ham natija bir xil.
#  2) Imtihon natijalari: coin BERILMAYDI (coins=0). Faqat natija
#     ko'chiriladi — o'quvchi o'z kabinetida ko'radi.
# =====================================================================
_LC_BAL_NOTE = "[LC UP] balans tenglashtirish"
_LC_EXAM_NOTE = "[LC UP]"


def _lc_phone(v) -> str:
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    if len(d) > 9 and d.startswith("998"):
        d = d[3:]
    elif len(d) == 10 and d.startswith("0"):
        d = d[1:]
    return d[-9:] if len(d) >= 9 else ""


def _lc_name(v) -> str:
    t = " ".join(str(v or "").split()).lower()
    for a, b in (("'", "'"), ("`", "'"), ("’", "'"), ("ʼ", "'")):
        t = t.replace(a, b)
    return t


def _lc_num(v) -> float:
    """«-1 388 000 so'm», «110 769», «1,388,000» -> float."""
    t = str(v or "").replace(" ", " ")
    neg = "-" in t
    d = "".join(ch for ch in t if ch.isdigit() or ch == ".")
    if not d:
        return 0.0
    try:
        x = float(d)
    except ValueError:
        return 0.0
    return -x if neg else x


def _lc_index(db: Session):
    """Telefon va ism bo'yicha qidiruv indeksi."""
    by_ph, by_nm = {}, {}
    for s in db.query(models.Student).all():
        p = _lc_phone(getattr(s, "phone", None))
        if p:
            by_ph.setdefault(p, s)
        by_nm.setdefault(_lc_name(s.full_name), s)
    return by_ph, by_nm


def _lc_match(row, by_ph, by_nm):
    s = by_ph.get(_lc_phone(row.get("phone")))
    if s is not None:
        return s, "telefon"
    s = by_nm.get(_lc_name(row.get("name")))
    return (s, "ism") if s is not None else (None, None)


@app.post("/api/lcup/balance")
def lcup_balance_sync(payload: dict = Body(...),
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.FULL_ACCESS))):
    """LC UP balanslarini yangi platformaga moslaydi.

    apply=false (standart) — hech narsa yozilmaydi, faqat farq
    ro'yxati qaytadi. apply=true — tenglashtirish yozuvlari qo'yiladi.
    """
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply"))
    by_ph, by_nm = _lc_index(db)
    seen, diffs, miss = set(), [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss.append({"name": r.get("name"), "phone": r.get("phone")})
            continue
        if s.id in seen:
            continue
        seen.add(s.id)
        target = _lc_num(r.get("balance"))
        # Eski tenglashtirishni hisobdan chiqarib, "toza" balansni olamiz
        old = (db.query(models.Payment)
               .filter(models.Payment.student_id == s.id,
                       models.Payment.note == _LC_BAL_NOTE).all())
        clean = M.student_balance(db, s.id) - sum(p.amount for p in old)
        diff = round(target - clean, 2)
        now = M.student_balance(db, s.id)
        item = {"student_id": s.id, "name": s.full_name, "how": how,
                "lcup": target, "hozir": round(clean, 2), "farq": diff,
                "balans": round(now, 2)}
        # Balans allaqachon LC UP dagidek bo'lsa — qayta yozmaymiz
        if abs(target - now) < 1:
            item["skip"] = "farq yo'q"
            diffs.append(item)
            continue
        diffs.append(item)
        if not apply:
            continue
        for p in old:
            db.delete(p)
        pay = models.Payment(
            student_id=s.id, amount=diff,
            kind="payment" if diff > 0 else "charge",
            note=_LC_BAL_NOTE, created_by=getattr(user, "full_name", None))
        db.add(pay)
        db.flush()
        M._ensure_public_id(db, "payment", pay)
    changed = [d for d in diffs if not d.get("skip")]
    if apply and changed:
        db.commit()
        audit.log(db, user, entity="payment", action="lcup_balance",
                  entity_label=f"LC UP: {len(changed)} ta balans",
                  new_value=len(changed), commit=True)
    return {"apply": apply, "kelgan": len(rows), "topildi": len(diffs),
            "o'zgargan": len(changed), "topilmadi": len(miss),
            "rows": changed[:500], "miss": miss[:300]}


@app.delete("/api/lcup/balance")
def lcup_balance_undo(db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.FULL_ACCESS))):
    """Tenglashtirishni bekor qiladi — hamma [LC UP] yozuvi o'chadi."""
    rows = (db.query(models.Payment)
            .filter(models.Payment.note == _LC_BAL_NOTE).all())
    for p in rows:
        db.delete(p)
    db.commit()
    audit.log(db, user, entity="payment", action="lcup_balance_undo",
              entity_label=f"{len(rows)} ta tenglashtirish o'chirildi",
              new_value=len(rows), commit=True)
    return {"deleted": len(rows)}


def _lc_group(db: Session, name: str):
    t = _lc_name(name)
    if not t:
        return None
    for g in db.query(models.Group).all():
        if _lc_name(g.name) == t:
            return g
    for g in db.query(models.Group).all():
        if t and (t in _lc_name(g.name) or _lc_name(g.name) in t):
            return g
    return None


@app.post("/api/lcup/exams")
def lcup_exams_import(payload: dict = Body(...),
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.FULL_ACCESS))):
    """LC UP imtihon natijalarini ko'chiradi. COIN BERILMAYDI.

    rows: [{group, exam, date, max, name, phone, score}]
    """
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply"))
    by_ph, by_nm = _lc_index(db)
    buckets, miss_st, miss_gr = {}, [], set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, _how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss_st.append(r.get("name"))
            continue
        key = (str(r.get("group") or ""), str(r.get("exam") or ""),
               str(r.get("date") or ""))
        buckets.setdefault(key, []).append((s, r))
    made_exams = made_rows = 0
    for (gname, ename, edate), items in buckets.items():
        g = _lc_group(db, gname)
        if g is None:
            g = next((it[0].group for it in items
                      if getattr(it[0], "group", None)), None)
        if g is None:
            miss_gr.add(gname)
            continue
        d = M._date_of(edate) if hasattr(M, "_date_of") else None
        if d is None:
            try:
                d = date.fromisoformat(str(edate)[:10])
            except Exception:
                d = date.today()
        mx = 0.0
        for _s, r in items:
            mx = max(mx, _lc_num(r.get("max")) or 0)
        if mx <= 0:
            mx = 100.0
        ex = (db.query(models.Exam)
              .filter(models.Exam.group_id == g.id,
                      models.Exam.title == ename,
                      models.Exam.date == d).first())
        if ex is None:
            if not apply:
                made_exams += 1
                made_rows += len(items)
                continue
            ex = models.Exam(group_id=g.id, kind="unit", title=ename,
                             date=d, max_score=mx, status="done",
                             note=_LC_EXAM_NOTE,
                             created_by=getattr(user, "full_name", None))
            db.add(ex)
            db.flush()
            made_exams += 1
        elif not apply:
            made_rows += len(items)
            continue
        have = {r.student_id for r in ex.results}
        for s, r in items:
            if s.id in have:
                continue
            sc = _lc_num(r.get("score"))
            db.add(models.ExamResult(
                exam_id=ex.id, student_id=s.id, score=sc, band=None,
                percent=round(sc / mx * 100, 1) if mx else None,
                coins=0,                      # <- coin berilmaydi
                absent=0, note=_LC_EXAM_NOTE,
                created_by=getattr(user, "full_name", None)))
            made_rows += 1
    if apply and (made_exams or made_rows):
        db.commit()
        audit.log(db, user, entity="exam", action="lcup_import",
                  entity_label=f"LC UP: {made_exams} imtihon, "
                               f"{made_rows} natija (coinsiz)",
                  new_value=made_rows, commit=True)
    return {"apply": apply, "imtihon": made_exams, "natija": made_rows,
            "guruh topilmadi": sorted(miss_gr)[:50],
            "o'quvchi topilmadi": len(miss_st)}


# LC UP ko'chirish moduli yuklandi (balans + imtihon, coinsiz).


# ---------------------------------------------------------------
# LC UP IMTIHONLARI v2: guruhni KO'PCHILIK bo'yicha aniqlash + bekor qilish
# Sabab: o'quvchilar guruhdan guruhga o'tgan. Birinchi mos tushgan
# o'quvchining guruhi ko'pincha xato bo'lib chiqadi (617 imtihondan 121 tasi).
# ---------------------------------------------------------------
_drop_route("/api/lcup/exams", "POST")


def _lc_pick_group(db: Session, items):
    """Mos tushgan o'quvchilarning ko'pchiligi qaysi guruhda — o'shani oladi."""
    tally = {}
    for st, _r in items:
        gg = getattr(st, "group", None)
        if gg is not None and getattr(gg, "id", None):
            tally[gg.id] = tally.get(gg.id, 0) + 1
    if not tally:
        return None
    best = max(tally.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    return (db.query(models.Group)
            .filter(models.Group.id == best).first())


@app.post("/api/lcup/exams")
def lcup_exams_import_v2(payload: dict = Body(...),
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.FULL_ACCESS))):
    """LC UP imtihon natijalarini ko'chiradi. COIN BERILMAYDI.

    rows: [{group, exam, date, max, name, phone, score}]
    """
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply"))
    by_ph, by_nm = _lc_index(db)
    buckets, miss_st, miss_gr = {}, [], set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, _how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss_st.append(r.get("name"))
            continue
        key = (str(r.get("group") or ""), str(r.get("exam") or ""),
               str(r.get("date") or ""))
        buckets.setdefault(key, []).append((s, r))
    made_exams = made_rows = 0
    for (gname, ename, edate), items in buckets.items():
        g = _lc_group(db, gname)
        if g is None:
            g = _lc_pick_group(db, items)
        if g is None:
            miss_gr.add(gname)
            continue
        d = M._date_of(edate) if hasattr(M, "_date_of") else None
        if d is None:
            try:
                d = date.fromisoformat(str(edate)[:10])
            except Exception:
                d = date.today()
        mx = 0.0
        for _s, r in items:
            mx = max(mx, _lc_num(r.get("max")) or 0)
        if mx <= 0:
            mx = 100.0
        ex = (db.query(models.Exam)
              .filter(models.Exam.group_id == g.id,
                      models.Exam.title == ename,
                      models.Exam.date == d).first())
        if ex is None:
            if not apply:
                made_exams += 1
                made_rows += len(items)
                continue
            ex = models.Exam(group_id=g.id, kind="unit", title=ename,
                             date=d, max_score=mx, status="done",
                             note=_LC_EXAM_NOTE,
                             created_by=getattr(user, "full_name", None))
            db.add(ex)
            db.flush()
            made_exams += 1
        elif not apply:
            made_rows += len(items)
            continue
        have = {r.student_id for r in ex.results}
        for s, r in items:
            if s.id in have:
                continue
            sc = _lc_num(r.get("score"))
            db.add(models.ExamResult(
                exam_id=ex.id, student_id=s.id, score=sc, band=None,
                percent=round(sc / mx * 100, 1) if mx else None,
                coins=0,                      # <- coin berilmaydi
                absent=0, note=_LC_EXAM_NOTE,
                created_by=getattr(user, "full_name", None)))
            have.add(s.id)
            made_rows += 1
    if apply and (made_exams or made_rows):
        db.commit()
        audit.log(db, user, entity="exam", action="lcup_import",
                  entity_label=f"LC UP: {made_exams} imtihon, "
                               f"{made_rows} natija (coinsiz)",
                  new_value=made_rows, commit=True)
    return {"apply": apply, "imtihon": made_exams, "natija": made_rows,
            "guruh topilmadi": sorted(miss_gr)[:50],
            "o'quvchi topilmadi": len(miss_st)}


@app.delete("/api/lcup/exams")
def lcup_exams_undo(db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FULL_ACCESS))):
    """LC UP dan ko'chirilgan imtihon natijalarini bekor qiladi."""
    res = (db.query(models.ExamResult)
           .filter(models.ExamResult.note == _LC_EXAM_NOTE).all())
    n_res = len(res)
    for x in res:
        db.delete(x)
    db.flush()
    n_ex = 0
    for e in (db.query(models.Exam)
              .filter(models.Exam.note == _LC_EXAM_NOTE).all()):
        if not e.results:
            db.delete(e)
            n_ex += 1
    db.commit()
    audit.log(db, user, entity="exam", action="lcup_undo",
              entity_label=f"LC UP importi bekor qilindi: {n_ex} imtihon, "
                           f"{n_res} natija",
              new_value=n_res, commit=True)
    return {"deleted_exams": n_ex, "deleted_results": n_res}


# ---------------------------------------------------------------
# LC UP: HAQIQIY TO'LOV TARIXI + TANGA BALANSI
# Faqat kvitansiyalar ko'chadi. LC UP o'zi hisoblagan yechimlar
# (oylik to'lov, aktivlashtirish, o'tkazish, muzlatish) ko'chirilmaydi —
# JonyOS o'z oyligini o'zi hisoblaydi, aks holda ikki marta yechiladi.
# ---------------------------------------------------------------
_LC_PAY_NOTE = "[LC UP] to'lov tarixi"
_LC_COIN_NOTE = "[LC UP] tanga ko'chirish"

_LC_METHOD = {
    "naqd pul": "cash", "naqd": "cash", "cash": "cash",
    "plastik karta": "card", "karta": "card", "card": "card",
    "terminal": "terminal",
    "bank hisobi": "other", "bank": "other", "o'tkazma": "other",
}


def _lc_method(v) -> str:
    return _LC_METHOD.get(_lc_name(v), "other")


def _lc_amt(v) -> float:
    """«480,000 so'm ( 13 dars )» -> 480000.0 (faqat oldingi son)."""
    t = " ".join(str(v or "").split()).replace(" ", " ")
    neg = t.lstrip().startswith("-")
    d = ""
    for ch in t:
        if ch.isdigit():
            d += ch
        elif ch in " ,":
            if d and not d.isdigit():
                break
            continue
        elif ch == "." and d:
            d += "."
        elif d:
            break
    if not d:
        return 0.0
    try:
        x = float(d)
    except ValueError:
        return 0.0
    return -x if neg else x


def _lc_date(v):
    """«Aug 11, 2026» yoki «2026-08-11» -> date."""
    from datetime import datetime as _dt
    s = " ".join(str(v or "").split())
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        pass
    for fmt in ("%b %d, %Y", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y"):
        try:
            return _dt.strptime(s, fmt).date()
        except Exception:
            continue
    return None


@app.post("/api/lcup/payments")
def lcup_payments_import(payload: dict = Body(...),
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.FULL_ACCESS))):
    """rows: [{name, phone, date, amount, method}] — kvitansiyalar."""
    from datetime import datetime as _dt
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply"))
    by_ph, by_nm = _lc_index(db)
    made = dup = bad = 0
    miss = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, _how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss.append(r.get("name"))
            continue
        amt = _lc_amt(r.get("amount"))
        d = _lc_date(r.get("date"))
        if amt <= 0 or d is None:
            bad += 1
            continue
        seen = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id,
                        models.Payment.note == _LC_PAY_NOTE,
                        models.Payment.amount == amt).all())
        if any(p.created_at and p.created_at.date() == d for p in seen):
            dup += 1
            continue
        if not apply:
            made += 1
            continue
        pay = models.Payment(
            student_id=s.id, amount=amt, kind="payment",
            method=_lc_method(r.get("method")), note=_LC_PAY_NOTE,
            created_by=getattr(user, "full_name", None))
        pay.created_at = _dt(d.year, d.month, d.day, 12, 0)
        db.add(pay)
        db.flush()
        M._ensure_public_id(db, "payment", pay)
        made += 1
    if apply and made:
        db.commit()
        audit.log(db, user, entity="payment", action="lcup_history",
                  entity_label=f"LC UP to'lov tarixi: {made} kvitansiya",
                  new_value=made, commit=True)
    return {"apply": apply, "yozildi": made, "takror": dup,
            "sana/summa xato": bad, "o'quvchi topilmadi": len(miss)}


@app.delete("/api/lcup/payments")
def lcup_payments_undo(db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.FULL_ACCESS))):
    """Ko'chirilgan to'lov tarixini bekor qiladi."""
    rows = (db.query(models.Payment)
            .filter(models.Payment.note == _LC_PAY_NOTE).all())
    n = len(rows)
    for p in rows:
        db.delete(p)
    db.commit()
    audit.log(db, user, entity="payment", action="lcup_history_undo",
              entity_label=f"LC UP to'lov tarixi bekor qilindi: {n}",
              new_value=n, commit=True)
    return {"deleted": n}


@app.post("/api/lcup/coins")
def lcup_coins_sync(payload: dict = Body(...),
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FULL_ACCESS))):
    """rows: [{name, phone, coins}] — tanga balansini tenglashtiradi."""
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply"))
    by_ph, by_nm = _lc_index(db)
    out, found, changed, miss = [], 0, 0, []
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss.append(r.get("name"))
            continue
        found += 1
        target = int(round(_lc_amt(r.get("coins"))))
        now = M._student_coin_balance(db, s.id)
        diff = target - now
        item = {"student_id": s.id, "name": s.full_name, "how": how,
                "lcup": target, "hozir": now, "farq": diff}
        if diff == 0:
            item["skip"] = "bir xil"
            out.append(item)
            continue
        changed += 1
        if apply:
            old = (db.query(models.CoinEntry)
                   .filter(models.CoinEntry.student_id == s.id,
                           models.CoinEntry.note == _LC_COIN_NOTE).first())
            if old is not None:
                old.amount = int(old.amount) + diff
            else:
                db.add(models.CoinEntry(
                    student_id=s.id, amount=diff, source="lcup",
                    note=_LC_COIN_NOTE,
                    created_by=getattr(user, "full_name", None)))
        out.append(item)
    if apply and changed:
        db.commit()
        audit.log(db, user, entity="student", action="lcup_coins",
                  entity_label=f"LC UP tanga: {changed} o'quvchi tenglashtirildi",
                  new_value=changed, commit=True)
    return {"apply": apply, "topildi": found, "o'zgargan": changed,
            "topilmadi": len(miss), "rows": out}


@app.delete("/api/lcup/coins")
def lcup_coins_undo(db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FULL_ACCESS))):
    """Ko'chirilgan tanga yozuvlarini bekor qiladi."""
    rows = (db.query(models.CoinEntry)
            .filter(models.CoinEntry.note == _LC_COIN_NOTE).all())
    n = len(rows)
    for c in rows:
        db.delete(c)
    db.commit()
    audit.log(db, user, entity="student", action="lcup_coins_undo",
              entity_label=f"LC UP tanga ko'chirish bekor qilindi: {n}",
              new_value=n, commit=True)
    return {"deleted": n}


# ---------------------------------------------------------------
# LC UP tanga: coin balansini main.py ga bog'lanmasdan hisoblash.
# Sabab: jonli serverda M._student_coin_balance topilmadi -> 500.
# ---------------------------------------------------------------
_drop_route("/api/lcup/coins", "POST")


def _lc_coin_bal(db: Session, sid: int) -> int:
    v = (db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
         .filter(models.CoinEntry.student_id == sid).scalar())
    return int(v or 0)


@app.post("/api/lcup/coins")
def lcup_coins_sync_v2(payload: dict = Body(...),
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.FULL_ACCESS))):
    """rows: [{name, phone, coins}] — tanga balansini tenglashtiradi."""
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    apply = bool(payload.get("apply") or payload.get("commit"))
    by_ph, by_nm = _lc_index(db)
    out, found, changed, miss = [], 0, 0, []
    for r in rows:
        if not isinstance(r, dict):
            continue
        s, how = _lc_match(r, by_ph, by_nm)
        if s is None:
            miss.append(r.get("name"))
            continue
        found += 1
        target = int(round(_lc_amt(r.get("coins"))))
        now = _lc_coin_bal(db, s.id)
        diff = target - now
        item = {"student_id": s.id, "name": s.full_name, "how": how,
                "lcup": target, "hozir": now, "farq": diff}
        if diff == 0:
            item["skip"] = "bir xil"
            out.append(item)
            continue
        changed += 1
        if apply:
            old = (db.query(models.CoinEntry)
                   .filter(models.CoinEntry.student_id == s.id,
                           models.CoinEntry.note == _LC_COIN_NOTE).first())
            if old is not None:
                old.amount = int(old.amount) + diff
            else:
                db.add(models.CoinEntry(
                    student_id=s.id, amount=diff, source="lcup",
                    note=_LC_COIN_NOTE,
                    created_by=getattr(user, "full_name", None)))
        out.append(item)
    if apply and changed:
        db.commit()
        audit.log(db, user, entity="student", action="lcup_coins",
                  entity_label=f"LC UP tanga: {changed} o'quvchi",
                  new_value=changed, commit=True)
    return {"apply": apply, "topildi": found, "o'zgargan": changed,
            "topilmadi": len(miss), "rows": out}


# ---------------------------------------------------------------
# LC UP: AYNAN BITTA O'QUVCHIGA (id bo'yicha) yozish.
# Bir xil ismli o'quvchilar bo'lganda ism/telefon bo'yicha topish
# ishlamaydi — bu yerda id aniq ko'rsatiladi.
# ---------------------------------------------------------------
@app.post("/api/lcup/by-id")
def lcup_by_id(payload: dict = Body(...),
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.FULL_ACCESS))):
    """payload: {student_id, payments:[{date,amount,method}], coins, balance, apply}"""
    from datetime import datetime as _dt
    sid = int(payload.get("student_id") or 0)
    s = (db.query(models.Student)
         .filter(models.Student.id == sid).first()) if sid else None
    if s is None:
        raise HTTPException(404, "O'quvchi topilmadi")
    apply = bool(payload.get("apply") or payload.get("commit"))
    made = dup = bad = 0
    for r in (payload.get("payments") or []):
        if not isinstance(r, dict):
            continue
        amt = _lc_amt(r.get("amount"))
        d = _lc_date(r.get("date"))
        if amt <= 0 or d is None:
            bad += 1
            continue
        seen = (db.query(models.Payment)
                .filter(models.Payment.student_id == sid,
                        models.Payment.note == _LC_PAY_NOTE,
                        models.Payment.amount == amt).all())
        if any(p.created_at and p.created_at.date() == d for p in seen):
            dup += 1
            continue
        if not apply:
            made += 1
            continue
        pay = models.Payment(
            student_id=sid, amount=amt, kind="payment",
            method=_lc_method(r.get("method")), note=_LC_PAY_NOTE,
            created_by=getattr(user, "full_name", None))
        pay.created_at = _dt(d.year, d.month, d.day, 12, 0)
        db.add(pay)
        db.flush()
        M._ensure_public_id(db, "payment", pay)
        made += 1
    coin = None
    if payload.get("coins") is not None:
        target = int(round(_lc_amt(payload.get("coins"))))
        now = _lc_coin_bal(db, sid)
        coin = {"lcup": target, "hozir": now, "farq": target - now}
        if apply and coin["farq"]:
            old = (db.query(models.CoinEntry)
                   .filter(models.CoinEntry.student_id == sid,
                           models.CoinEntry.note == _LC_COIN_NOTE).first())
            if old is not None:
                old.amount = int(old.amount) + coin["farq"]
            else:
                db.add(models.CoinEntry(
                    student_id=sid, amount=coin["farq"], source="lcup",
                    note=_LC_COIN_NOTE,
                    created_by=getattr(user, "full_name", None)))
    bal = None
    if payload.get("balance") is not None:
        target = _lc_amt(payload.get("balance"))
        if apply:
            db.flush()
        now = M.student_balance(db, sid)
        bal = {"lcup": target, "hozir": now, "farq": round(target - now, 2)}
        if apply and abs(bal["farq"]) >= 1:
            p = models.Payment(
                student_id=sid, amount=bal["farq"],
                kind="payment" if bal["farq"] > 0 else "charge",
                method="other" if bal["farq"] > 0 else None,
                note=_LC_BAL_NOTE, created_by=getattr(user, "full_name", None))
            db.add(p)
            db.flush()
            M._ensure_public_id(db, "payment", p)
    if apply:
        db.commit()
        audit.log(db, user, entity="student", action="lcup_by_id",
                  entity_id=sid, entity_label=f"LC UP (id bo'yicha): "
                  f"{s.full_name} — {made} to'lov",
                  new_value=made, commit=True)
    return {"apply": apply, "student": s.full_name, "student_id": sid,
            "to'lov yozildi": made, "takror": dup, "xato qator": bad,
            "tanga": coin, "balans": bal}


# =====================================================================
#  OYLIK TO'LOV — YANGI QOIDA (Jahongir tasdiqlagan)
#
#  Avval: summa O'TILGAN darsdan hisoblanardi, shuning uchun oyning
#  1-kuni 0 chiqib hech kimdan yechilmasdi; birinchi dars o'tilgan kuni
#  esa faqat 1 dars uchun yechilardi va "bu oy bajarildi" degan UMUMIY
#  belgi qolgan hamma o'quvchini oy oxirigacha chetda qoldirardi.
#
#  Endi: har oyning 1-kuni 05:00 (Toshkent)da har bir faol o'quvchidan
#  TO'LIQ standart oylik yechiladi (standart dars soni x dars narxi).
#  Oy tugagach, agar dars kam o'tilgan bo'lsa, farq avtomat qaytariladi
#  (chegirma yozuvi). Tekshiruv har bir o'quvchi bo'yicha alohida —
#  bitta guruh yechilgani boshqasini to'xtatib qo'ymaydi.
#
#  Avgust 2026 va undan oldingi oylarga tegilmaydi (qo'lda kiritilgan).
# =====================================================================
_MC_BY = "avtomat (oylik)"
_MC_BACK = "farq qaytarildi"
_MC_FROM = "2026-09"          # shu oydan boshlab yangi qoida ishlaydi


def _mc_key(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}"


def _mc_has_charge(db: Session, sid: int, period: str) -> bool:
    """Shu o'quvchidan shu oy uchun allaqachon yechilgan (qo'lda,
    faollashtirishda yoki avtomat) — ikkinchi marta yechilmaydi."""
    return (db.query(models.Payment)
            .filter(models.Payment.student_id == sid,
                    models.Payment.kind == "charge",
                    models.Payment.period == period)
            .first() is not None)


def _mc_active_groups(db: Session):
    """Faol o'quvchisi bor guruhlar. 2026-08-14: ilgari har guruh
    uchun alohida so'rov ketardi (100 guruh = 100 so'rov), endi
    hammasi BITTA so'rovda olinadi."""
    ids = [gid for (gid,) in
           db.query(models.Student.group_id)
           .filter(models.Student.status == "active",
                   models.Student.group_id.isnot(None))
           .distinct().all()]
    if not ids:
        return []
    return (db.query(models.Group)
            .filter(models.Group.id.in_(ids))
            .order_by(models.Group.id).all())


def _mc_charge_full(db: Session, today, deadline=None) -> tuple:
    """1-kundan boshlab: har bir faol o'quvchidan to'liq standart oylik.

    2026-08-14 (Jahongir: "Guruhlar ko'paysa yarmida uzilib, oyning
    bir qismi hisoblanmay qolishi mumkin"): endi HAR GURUH alohida
    belgilanadi va vaqt byudjeti tugasa funksiya to'xtaydi — keyingi
    chaqiruv aynan QOLGAN guruhlardan davom etadi. Qaytaradi:
    (nechta yozuv, hammasi tugadimi)."""
    import time as _time
    import billing as _B  # noqa: F401  (kelgusida kerak bo'ladi)
    from common import _seed_done as _sd, _seed_mark as _sm
    period = _mc_key(today.year, today.month)
    n = 0
    finished = True
    for g in _mc_active_groups(db):
        gkey = f"mcf_{period}_g{g.id}"
        if _sd(db, gkey):
            continue
        if deadline is not None and _time.monotonic() > deadline:
            finished = False
            continue
        price = float(g.lesson_price or 0)
        std = int(g.standard_lessons_per_month or 12)
        if roles.money(price * std) <= 0:
            _sm(db, gkey)      # narxi yo'q guruh — qayta urinmaymiz
            continue
        students = (db.query(models.Student)
                    .filter(models.Student.group_id == g.id,
                            models.Student.status == "active").all())
        for s in students:
            # ESKI NARX HIMOYASI: o'quvchida qulflangan narx bo'lsa
            # o'sha ishlaydi (2026-08-15)
            full = roles.money(_billing.student_lesson_price(s, g) * std)
            # CHEGIRMA (2026-09-06). Ilgari avtomat yechim chegirmani
            # UMUMAN ko'rmasdi: oilaviy 10%, xodim farzandi va
            # individual chegirmalar faqat faollashtirish/muzlatish/
            # ko'chirish qayta hisoblarida ishlardi. Natijada chegirmali
            # o'quvchidan oy boshida TO'LIQ narx yechilardi va admin
            # qo'lda tuzatishga majbur bo'lardi.
            full = _mc_after_discount(db, s, full)
            if full <= 0:
                continue
            # Shu oy ichida qo'shilgan bo'lsa — faollashtirish yozuvi
            # allaqachon o'z ulushini yechgan, aralashmaymiz.
            if s.enrolled_date and _mc_key(
                    s.enrolled_date.year, s.enrolled_date.month) == period:
                continue
            if _mc_has_charge(db, s.id, period):
                continue
            if M._charge_skipped(db, s.id, period):
                continue
            db.add(models.Payment(
                student_id=s.id, amount=-full, kind="charge",
                note=f"{g.name} — {period}: {std} dars (standart oy, avtomat)",
                created_by=_MC_BY, period=period))
            n += 1
        # Guruh to'liq ishlandi — belgilaymiz va saqlaymiz. Shundan
        # keyin bu guruh qayta ko'rilmaydi (ikki marta yechish yo'q).
        try:
            db.commit()
            _sm(db, gkey)
        except Exception:
            db.rollback()
            finished = False
    return n, finished


def _mc_charge_missed(db: Session, today) -> list:
    """XAVFSIZLIK TO'RI (2026-09-16, Jahongir: "bazi o'quvchilar faol
    bolsa ham pul yechilmayabdi shuni togrla").

    Faol, guruhi bor, lekin SHU OY uchun hech qanday hisob yozilmagan
    o'quvchilar. Ular quyidagi yo'llardan paydo bo'lardi: liddan
    to'g'ridan-to'g'ri "faol" qilib ochilgan (oylik yechilmagan), oy
    boshidagi avtomat yechimdan KEYIN faollashgan va h.k.

      - shu oy qo'shilgan (enrolled_date) — qo'shilgan kunidan oy
        oxirigacha (faollashtirish qoidasi);
      - oldinroq qo'shilgan — to'liq standart oy (oy boshidagi avtomat
        yechim qoidasi), lekin faqat guruhi shu oy allaqachon
        ishlangan bo'lsa (aks holda buni _mc_charge_full o'zi qiladi).

    Asoschi o'chirgan yechim (ChargeSkip) QAYTA YOZILMAYDI."""
    from common import _seed_done as _sd
    period = _mc_key(today.year, today.month)
    if period < _MC_FROM:
        return []
    charged = (db.query(models.Payment.student_id)
               .filter(models.Payment.kind == "charge",
                       models.Payment.period == period))
    skipped = (db.query(models.ChargeSkip.student_id)
               .filter(models.ChargeSkip.period == period))
    students = (db.query(models.Student)
                .filter(models.Student.status == "active",
                        models.Student.group_id.isnot(None),
                        models.Student.id.notin_(charged),
                        models.Student.id.notin_(skipped))
                .all())
    done = []
    for s in students:
        g = s.group
        if g is None:
            continue
        res = None
        if s.enrolled_date and _mc_key(
                s.enrolled_date.year, s.enrolled_date.month) == period:
            res = _charge_from_activation_v2(db, s, s.enrolled_date, None)
        elif _sd(db, f"mcf_{period}_g{g.id}"):
            std = int(g.standard_lessons_per_month or 12) or 12
            full = _mc_after_discount(
                db, s, roles.money(_billing.student_lesson_price(s, g) * std))
            if full > 0:
                db.add(models.Payment(
                    student_id=s.id, amount=-full, kind="charge",
                    note=f"{g.name} — {period}: {std} dars (standart oy, avtomat)",
                    created_by=_MC_BY, period=period))
                res = {"amount": full}
        if res:
            done.append({"student_id": s.id, "name": s.full_name,
                         "amount": roles.money(res["amount"])})
    if done:
        db.commit()
        audit.log(db, None, entity="payment", action="create",
                  entity_label=f"{period}: yechilmay qolgan oyliklar",
                  new_value=len(done),
                  note=", ".join(f"{d['name']} {int(d['amount'])}"
                                 for d in done[:40]),
                  commit=True)
    return done


_RA_DATE = __import__("re").compile(r"(\d{4}-\d{2}-\d{2})")


def _mc_reactivated_after_skip(db: Session, today) -> list:
    """QAYTIB KELGANDA YECHILMAY QOLGAN OYLIK (2026-09-28, Jahongir:
    "mana bu o'quvchi 3 ta darsdan beri kelyabdi lekin pul yechilmagan
    ... shunaqa holatlar yana bormikan sababini topib tuzat").

    Sabab: asoschi kelmay turgan o'quvchining oylik yechimini o'chirsa,
    shu oy uchun ChargeSkip yoziladi. O'quvchi keyin (shu oyning o'zida)
    qaytib faollashsa, eski kod skip'ni ko'rib faollashish yechimini
    ham yozmasdi — kunlik xavfsizlik to'ri ham skip'lilarni chetlab
    o'tadi. Natijada o'quvchi oy oxirigacha tekin o'qirdi.

    Faollashish kodi tuzatildi (_charge_from_activation_v2 honor_skip),
    bu esa OLDIN qolib ketganlarini ham ushlaydi va bundan keyin ham
    kunlik to'r bo'lib turadi. Shart — hammasi bir vaqtda:
      * o'quvchi hozir FAOL va guruhi bor;
      * shu oy uchun ChargeSkip bor va shu oy yechimi YO'Q;
      * skip'dan KEYIN faollashtirilgan (audit: student/activate).
    Yechim faollashish sanasidan oy oxirigacha (oddiy faollashish
    qoidasi bilan bir xil). Skip o'chirilmaydi; asoschi yangi yozuvni
    ham o'chirsa — keyingi faollashishgacha qayta yozilmaydi (yangi
    skip faollashishdan keyin bo'ladi)."""
    from datetime import timedelta as _td
    period = _mc_key(today.year, today.month)
    if period < _MC_FROM:
        return []
    last_skip = {}
    for k in (db.query(models.ChargeSkip)
              .filter(models.ChargeSkip.period == period).all()):
        t = k.created_at
        if t is None:
            last_skip[k.student_id] = None       # sanasiz — tegilmaydi
            continue
        if k.student_id in last_skip and last_skip[k.student_id] is None:
            continue
        if k.student_id not in last_skip or t > last_skip[k.student_id]:
            last_skip[k.student_id] = t
    if not last_skip:
        return []
    ids = [sid for sid, t in last_skip.items() if t is not None]
    if not ids:
        return []
    charged = {sid for (sid,) in
               db.query(models.Payment.student_id)
               .filter(models.Payment.kind == "charge",
                       models.Payment.period == period,
                       models.Payment.student_id.in_(ids)).all()}
    start, _end = M.billing.month_bounds(today.year, today.month)
    done = []
    for sid in ids:
        if sid in charged:
            continue
        s = db.query(models.Student).get(sid)
        if s is None or s.status != "active" or not s.group_id \
                or s.group is None:
            continue
        act = (db.query(models.AuditLog)
               .filter(models.AuditLog.entity == "student",
                       models.AuditLog.entity_id == sid,
                       models.AuditLog.action == "activate",
                       models.AuditLog.created_at > last_skip[sid])
               .order_by(models.AuditLog.created_at.desc()).first())
        if act is None:
            continue
        on = None
        m = _RA_DATE.search(act.note or "")
        if m:
            try:
                on = date.fromisoformat(m.group(1))
            except ValueError:
                on = None
        if on is None:
            on = (act.created_at + _td(hours=5)).date()   # Toshkent
        if on < start:
            on = start
        if on > today:
            continue
        res = _charge_from_activation_v2(db, s, on, None, honor_skip=False)
        if res:
            done.append({"student_id": sid, "name": s.full_name,
                         "since": on.isoformat(),
                         "lessons": res["lessons"],
                         "amount": roles.money(res["amount"])})
    if done:
        db.commit()
        audit.log(db, None, entity="payment", action="create",
                  entity_label=f"{period}: qaytib kelganlarning oyligi",
                  new_value=len(done),
                  note="; ".join(f"{d['name']} {d['since']} dan "
                                 f"{d['lessons']} dars {int(d['amount'])}"
                                 for d in done[:40]),
                  commit=True)
    return done


_MC_OLD_FIX = "to'liq oyga to'g'rilandi"


def _mc_fix_old_rule(db: Session, today, apply: bool = True) -> list:
    """ESKI QOIDA BILAN YOZILGAN OYLIK (2026-10-02, Jahongir: "58 ta
    o'quvchi 40 ta qarzdor ... ba'zilaridan yechilgan, ba'zilaridan
    esa bitta darsga yechilgan").

    Sabab: 27-sentabrdagi bo'linishdan keyin login (auth_users.py)
    yangi qoidaga ulanmay qolgan edi. 1-oktabr 05:00 dan keyingi
    birinchi kirishda ESKI common._ensure_month_charges ishladi —
    u "o'tilgan darslar" bo'yicha yechadi: shu paytgacha 1 dars
    o'tilgan guruhlardan 1 dars uchun yechdi. Yangi qoida esa
    "shu oy yechimi bor" deb ularni o'tkazib yubordi. Darsi hali
    o'tilmagan guruhlar eski qoidada "kutilmoqda" bo'lib qoldi va
    yangi qoida ulardan to'liq oylikni yechdi — shu sabab natija
    aralash chiqdi.

    Bu funksiya eski qoida yozgan qatorlarni (izohi "<guruh> - <oy>
    oyi uchun N dars (avtomat)") to'liq oylik summaga (chegirmasi bo'lsa
    chegirma bilan) JOYIDA ko'taradi — qator o'chirilmaydi, eski summa
    auditda qoladi.
    Faqat KO'TARADI; qo'lda o'zgartirilgan yoki allaqachon to'g'ri
    qatorga tegmaydi. Idempotent."""
    period = _mc_key(today.year, today.month)
    if period < _MC_FROM:
        return []
    rows = (db.query(models.Payment)
            .filter(models.Payment.period == period,
                    models.Payment.kind == "charge",
                    models.Payment.created_by == _MC_BY,
                    models.Payment.note.like(f"% - {period} oyi uchun %"))
            .all())
    done = []
    for p in rows:
        if _MC_OLD_FIX in (p.note or ""):
            continue
        s = db.query(models.Student).get(p.student_id)
        if s is None or s.status != "active" or s.group is None:
            continue
        g = s.group
        # Qator boshqa guruh uchun yozilgan bo'lsa (o'quvchi ko'chgan) —
        # qo'lda ko'rilsin
        if not (p.note or "").startswith(f"{g.name} - "):
            continue
        # Jahongir (2026-10-02): "har biridan avtomat oylik summa
        # yechilsin, chegirmasi bo'lsa chegirma bilan, bo'lmasa to'liq"
        std = int(g.standard_lessons_per_month or 12) or 12
        want = _mc_expected(db, s, g, std)
        what = f"{std} dars (standart oy)"
        old = abs(float(p.amount or 0))
        if want <= old + 0.5:
            continue
        done.append({"student_id": s.id, "name": s.full_name,
                     "branch_id": s.branch_id,
                     "old": roles.money(old), "new": roles.money(want)})
        if not apply:
            continue
        old_amt = p.amount
        p.amount = -want
        p.note = ((p.note or "") + f" · {_MC_OLD_FIX}: {what}, "
                  f"{int(old):,} -> {int(want):,}").replace(",", " ")
        p.updated_at = _dt_now()
        audit.log(db, None, entity="payment", action="update",
                  entity_id=p.id, entity_label=s.full_name,
                  field="amount", old_value=old_amt, new_value=-want,
                  note="Oy boshida eski qoida bilan faqat o'tilgan "
                       "darslar yechilgan edi — to'liq oyga to'g'rilandi",
                  branch_id=s.branch_id)
    if apply and done:
        db.commit()
        audit.log(db, None, entity="payment", action="update",
                  entity_label=f"{period}: chala yechilgan oyliklar "
                               f"to'g'rilandi",
                  new_value=len(done),
                  note=", ".join(f"{d['name']} {int(d['old'])}->"
                                 f"{int(d['new'])}" for d in done[:40]),
                  commit=True)
    return done


def _dt_now():
    from datetime import datetime as _d
    return _d.utcnow()


def _mc_after_discount(db: Session, s, amount: float) -> float:
    """Chegirma qo'llangan summa (2026-09-06).

    Jahongir: "toglrla hamma aytganingni" — auditda topilgan xato:
    avtomat oylik yechim chegirmani hisobga olmasdi. Endi bitta joyda:
    oilaviy + tasdiqlangan chegirmalar foizi (common._student_discount_percent
    — u chegaralarni ham o'zi qo'llaydi) ayiriladi. Xato bo'lsa summa
    O'ZGARMAY qaytadi: chegirma o'qilmagani uchun pul yo'qolmasin."""
    try:
        disc = float(M._student_discount_percent(db, s) or 0)
    except Exception:
        return amount
    if disc <= 0:
        return amount
    return roles.money(amount * (1 - min(disc, 100.0) / 100.0))


def _mc_expected(db: Session, s, g, std: int) -> float:
    """Shu oy uchun kutilayotgan to'liq hisob (chegirma bilan)."""
    return _mc_after_discount(
        db, s, roles.money(_billing.student_lesson_price(s, g) * (std or 12)))


def fix_discount_charges(db: Session, period: str = None,
                         apply: bool = True) -> dict:
    """Chegirma hisobga olinmay yechilgan oylik hisoblarni to'g'rilaydi.

    FAQAT avtomat yozuvlar (created_by = _MC_BY) va faqat _MC_FROM dan
    keyingi oylar ko'riladi. Qator O'CHIRILMAYDI — summa JOYIDA
    to'g'rilanadi (tizimdagi boshqa tuzatishlar bilan bir xil qoida:
    _fz_set, edit_payment, sentabr narx qoidasi), eski summa auditda
    qoladi. Kamaytirish ham, oshirish ham mumkin emas — faqat
    chegirmasiz yozilgan qatorni chegirmali summaga tushiradi
    (ya'ni o'quvchi foydasiga)."""
    out = {"period": period, "checked": 0, "fixed": 0, "sum": 0.0,
           "rows": []}
    if period is None:
        _t = roles.local_today()
        period = _mc_key(_t.year, _t.month)
    if period < _MC_FROM:
        return out
    rows = (db.query(models.Payment)
            .filter(models.Payment.period == period,
                    models.Payment.kind == "charge",
                    models.Payment.created_by == _MC_BY).all())
    for p in rows:
        s = db.query(models.Student).get(p.student_id)
        if s is None or s.group is None:
            continue
        out["checked"] += 1
        g = s.group
        std = int(g.standard_lessons_per_month or 12) or 12
        full = roles.money(_billing.student_lesson_price(s, g) * std)
        want = _mc_after_discount(db, s, full)
        # Faqat "chegirmasiz yozilgan" holat: hozirgi summa to'liq
        # narxga teng, kutilgani esa undan kam.
        if want >= full - 0.5:
            continue
        if abs(abs(p.amount) - full) > 0.5:
            continue          # boshqa sabab bilan o'zgartirilgan — tegmaymiz
        diff = roles.money(full - want)
        out["rows"].append({
            "student_id": s.id, "name": s.full_name,
            "branch": s.branch.name if s.branch else None,
            "old": roles.money(full), "new": roles.money(want),
            "back": diff,
        })
        out["fixed"] += 1
        out["sum"] = roles.money(out["sum"] + diff)
        if not apply:
            continue
        old_amt = p.amount
        p.amount = -want
        p.note = ((p.note or "") + f" · chegirma tuzatildi: "
                  f"{int(full):,} -> {int(want):,}").replace(",", " ")
        p.updated_at = _dt_now()
        audit.log(db, None, entity="payment", action="update",
                  entity_id=p.id, entity_label=s.full_name,
                  field="amount", old_value=old_amt, new_value=-want,
                  note="Avtomat oylik yechimda chegirma qo'llanmagan edi",
                  branch_id=s.branch_id)
    if apply and out["fixed"]:
        db.commit()
    return out


def _mc_refund_prev(db: Session, today, deadline=None) -> tuple:
    """O'tgan oy uchun: dars kam o'tilgan bo'lsa farqni qaytaradi.
    Vaqt byudjeti tugasa to'xtaydi — qaytarilmaganlari keyingi
    chaqiruvda ko'riladi (allaqachon qaytarilgani qayta ko'rilmaydi,
    izohdagi belgi bo'yicha).

    O'CHIRILGAN (2026-10-02, Jahongir: "Qaytarilmasin" — qoida: oyda
    dars soni qancha bo'lsa ham bir xil to'liq oylik, kamida 12 dars
    puli). 1-oktabrda bu funksiya sentabr uchun "+summa chegirma"
    qatorlarini yozgan edi: yo'qlamasi qo'yilmagan darslar "o'tilmagan"
    sanalgan, o'quvchi guruh almashgan bo'lsa esa HOZIRGI guruh darslari
    sanalgan. Ota-onalar buni "pul to'langan" deb tushungan. Yozilganlari
    lesson_refund_rows ro'yxatida ko'rib chiqiladi."""
    return 0, True
    import time as _time
    from datetime import timedelta as _td
    import billing as _B
    first = date(today.year, today.month, 1)
    prev_end = first - _td(days=1)
    period = _mc_key(prev_end.year, prev_end.month)
    if period < _MC_FROM:
        return 0, True
    rows = (db.query(models.Payment)
            .filter(models.Payment.period == period,
                    models.Payment.kind == "charge",
                    models.Payment.created_by == _MC_BY).all())
    n = 0
    finished = True
    for p in rows:
        if deadline is not None and _time.monotonic() > deadline:
            finished = False
            break
        s = (db.query(models.Student)
             .filter(models.Student.id == p.student_id).first())
        if s is None or s.group is None:
            continue
        done = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id,
                        models.Payment.period == period,
                        models.Payment.note.like("%" + _MC_BACK + "%"))
                .first())
        if done is not None:
            continue
        g = s.group
        price = _billing.student_lesson_price(s, g)
        held = _B.billable_lessons_for_student(
            db, s, g, prev_end.year, prev_end.month)
        actual = _mc_after_discount(db, s, roles.money(price * held))
        back = roles.money(abs(p.amount) - actual)
        if back < 1:
            continue
        db.add(models.Payment(
            student_id=s.id, amount=back, kind="discount",
            note=f"{g.name} — {period}: {held} dars o'tildi, {_MC_BACK}",
            created_by=_MC_BY, period=period))
        n += 1
    if n:
        try:
            db.commit()
        except Exception:
            db.rollback()
            finished = False
    return n, finished


def _dsc_fix_month(db: Session, today) -> list:
    """CHEGIRMASI BOR, LEKIN HISOBI CHEGIRMASIZ QOLGANLAR (2026-09-25).

    Jahongir: "10% chegirma yechib olmayabdi". Sababi ikkita edi va
    ikkalasi ham tuzatildi (finance.create_discount endi darhol
    amaldagi chegirmada ham hisobni qayta yozadi; qisman oy hisobi
    ham tuzatiladi). Bu funksiya ESKI, allaqachon qolib ketgan
    qatorlarni to'g'rilaydi — oyiga bir marta.

    Ishonchli: hisobni finance._recharge_current_month() ning O'ZI
    yozadi, ya'ni qoida bitta joyda. U faqat KAMAYTIRADI va chegirma
    allaqachon qo'llangan qatorga tegmaydi."""
    period = _mc_key(today.year, today.month)
    if period < _MC_FROM:
        return []
    import finance as _F
    sids = [sid for (sid,) in
            db.query(models.Discount.student_id)
            .filter(models.Discount.status == "active").distinct().all()]
    if not sids:
        return []
    done = []
    for chunk in _billing._chunks(sids) if hasattr(_billing, "_chunks") \
            else [sids]:
        rows = (db.query(models.Student)
                .filter(models.Student.id.in_(chunk),
                        models.Student.group_id.isnot(None),
                        models.Student.status == "active").all())
        for s in rows:
            has = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
            if has is None:
                continue
            before = abs(float(has.amount or 0))
            try:
                if _F._recharge_current_month(db, s):
                    done.append({"student_id": s.id, "name": s.full_name,
                                 "old": before})
            except Exception:
                db.rollback()
    if done:
        audit.log(db, None, entity="payment", action="update",
                  entity_label=f"{period}: chegirma qo'llanmagan hisoblar",
                  new_value=len(done),
                  note=", ".join(d["name"] for d in done[:40]), commit=True)
    return done


def _fix_washington_teacher(db: Session) -> int:
    """BIR MARTALIK (2026-10-03, Jahongir tasdiqladi: "hop"). Bekobod 1
    Washington guruhiga adashib Zafardan ketgan "Xoshimova Rayxona"
    tanlangan edi; guruh keyin Rayxona Abdujalilovaga to'g'rilangan, lekin
    sentabr darslari Xoshimovada qolgan. O'sha darslar guruhning hozirgi
    ustoziga o'tadi va sentabr oyligi muhri qayta hisoblanadi.
    Xavfsizlik: guruhning hozirgi ustozi Abdujalilova bo'lsagina."""
    from sqlalchemy import func as _f
    b = db.query(models.Branch).filter(
        _f.lower(models.Branch.name) == "bekobod 1").first()
    if not b:
        return 0
    g = db.query(models.Group).filter(
        models.Group.branch_id == b.id,
        _f.lower(models.Group.name) == "washington").first()
    new = db.query(models.Teacher).get(g.teacher_id) if g and g.teacher_id else None
    if not g or not new or "abdujalilova" not in (new.full_name or "").lower():
        return 0
    olds = [t for t in db.query(models.Teacher).all()
            if "xoshimova" in (t.full_name or "").lower()
            and "rayxona" in (t.full_name or "").lower()]
    if not olds:
        return 0
    old_ids = [t.id for t in olds]
    les = db.query(models.Lesson).filter(
        models.Lesson.group_id == g.id,
        models.Lesson.teacher_id.in_(old_ids),
        models.Lesson.date >= date(2026, 9, 1)).all()
    for l in les:
        l.teacher_id = new.id
    db.commit()
    if les:
        audit.log(db, None, entity="group", action="update", entity_id=g.id,
                  entity_label=g.name, branch_id=g.branch_id,
                  field="darslar ustozi",
                  old_value=", ".join(t.full_name for t in olds),
                  new_value=new.full_name,
                  note=f"{len(les)} ta dars (sentabrdan) — adashib tanlangan "
                       "ustozdan guruhning hozirgi ustoziga", commit=True)
        # Sentabr muhri FAQAT shu ikki ustozniki qayta hisoblanadi
        # (boshqa ustozlar muhriga tegilmaydi): eskisi o'chadi, keyin
        # _seal_month muhri yo'qlarnigina muhrlaydi; darsi qolmagan
        # Xoshimovaga yangi muhr tushmaydi.
        db.query(models.PayrollSeal).filter(
            models.PayrollSeal.period == "2026-09",
            models.PayrollSeal.teacher_id.in_(old_ids + [new.id])).delete(
                synchronize_session=False)
        db.commit()
        _C._seal_month(db, 2026, 9, by="tuzatish (Washington)")
    return len(les)


def _salary_period_fix(db: Session, d0, d1, to_period: str) -> int:
    """[d0, d1] kunlari berilgan oyliklarni (avans emas) to_period ga
    o'tkazadi: ustoz (TeacherPayment), examiner/support
    (StaffSalaryPayment), xodim (Xarajat -> Oylik)."""
    cur = d0.strftime("%Y-%m")
    n = 0
    for p in db.query(models.TeacherPayment).filter(
            models.TeacherPayment.paid_on >= d0,
            models.TeacherPayment.paid_on <= d1,
            models.TeacherPayment.kind != "advance").all():
        if p.period in (None, "", cur):
            p.period = to_period
            n += 1
    SSP = getattr(models, "StaffSalaryPayment", None)
    if SSP is not None:
        for p in db.query(SSP).filter(SSP.paid_on >= d0, SSP.paid_on <= d1,
                                      SSP.kind != "advance").all():
            if p.period in (None, "", cur):
                p.period = to_period
                n += 1
    for e in db.query(models.Expense).filter(
            models.Expense.staff_user_id.isnot(None),
            models.Expense.date >= d0, models.Expense.date <= d1).all():
        if e.period in (None, "", cur):
            e.period = to_period
            n += 1
    db.commit()
    return n


def _mc_ensure(db: Session, _orig=None, budget_s: float = 8.0):
    """Login va kunlik cron shu funksiyani chaqiradi.

    2026-08-14: VAQT BYUDJETI bilan ishlaydi. Login yo'lida kichik
    (5 s), cron'da katta (24 s) — Vercel'ning 30 soniyalik limitiga
    urilib yarim yo'lda uzilib qolmaydi. Tugallanmagan qismi keyingi
    chaqiruvda AYNAN QOLGAN JOYIDAN davom etadi (guruh belgilari).
    Ikkinchi nusxa esa kutib turmaydi — try_lock bilan chetga chiqadi,
    shunda navbat yig'ilmaydi."""
    import time as _time
    now = roles.local_now()
    today = now.date()
    if today.day == 1 and now.hour < 5:
        return
    period = _mc_key(today.year, today.month)
    if period < _MC_FROM:
        # Eski oylar — avvalgi mantiq (tegilmaydi).
        if _orig is not None:
            try:
                return _orig(db, budget_s=budget_s)
            except TypeError:
                return _orig(db)
            except Exception:
                return
        return

    from common import _seed_done as _sd, _seed_mark as _sm
    # Umumiy "bo'ldi" bayrog'i ATAYLAB yo'q — oy o'rtasida ochilgan
    # YANGI guruh ham hisoblanishi kerak. Har guruh alohida
    # belgilanadi (mcf_<oy>_g<id>), qaytarish esa oyiga bir marta.
    refund_key = f"mcr_{period}"
    # Yechilmay qolganlarni tekshirish — kuniga bir marta (2026-09-16)
    # "mcm2" (2026-10-05): kalit yangilandi — bugun guruh qo'shish
    # yo'li bilan yechilmay qolganlar (Rahmanova Diyora) deploydan
    # keyin shu kunning o'zida ushlansin. Idempotent: faqat shu oy
    # hisobi yo'q faol o'quvchilarga tegadi.
    missed_key = f"mcm2_{today.isoformat()}"
    # Chegirmasi bor, lekin shu oy hisobi chegirmasiz qolganlar —
    # oyiga bir marta (2026-09-25, Jahongir: "10% chegirma yechib
    # olmayabdi"). Sababi tuzatildi; bu esa ESKI qolib ketganlarini
    # ham to'g'rilaydi.
    dsc_key = f"dscfix_{period}"
    # Skip'dan keyin qaytib faollashganlar — kuniga bir marta
    # (2026-09-28, _mc_reactivated_after_skip izohiga qarang)
    ra_key = f"mcra_{today.isoformat()}"
    old_key = f"mcold_{today.isoformat()}"
    # BIR MARTALIK (2026-10-02, Jahongir: "kam dars qaytarilgan farq
    # bo'lsa bu chegirmalarni olib tashla") — 1-oktabrda o'chirilgan
    # _mc_refund_prev yozgan "+summa chegirma" qatorlari arxivga.
    # BIR MARTALIK (2026-10-03, Jahongir: "sentabr oyinikini oktabrda
    # berilsa ham sentabrniki bo'lib yozilsin") — 1–15 oktabrda berilgan
    # oyliklar (avans emas) sentabrniki bo'ladi.
    wf_key = "fix_washington_teacher_2026-10"
    if not _sd(db, wf_key):
        try:
            _n = _fix_washington_teacher(db)
            _sm(db, wf_key)
            if _n:
                print(f"[oylik] Washington darslari to'g'rilandi: {_n}")
        except Exception:
            db.rollback()
    sp_key = "salary_period_fix_2026-10"
    if not _sd(db, sp_key):
        try:
            _n = _salary_period_fix(db, date(2026, 10, 1), date(2026, 10, 15),
                                    "2026-09")
            _sm(db, sp_key)
            if _n:
                audit.log(db, None, entity="salary", action="period_fix",
                          entity_label="Oktabr boshida berilgan oyliklar "
                                       "sentabrniki qilindi",
                          new_value=_n, commit=True)
                print(f"[oylik] sentabrga o'tkazilgan to'lovlar: {_n}")
        except Exception:
            db.rollback()
    lr_key = "lrfix_cancel_2026-10"
    if not _sd(db, lr_key):
        try:
            import finance as _Fin
            _lr = _Fin._lesson_refund_cancel_all(db)
            _sm(db, lr_key)
            if _lr:
                audit.log(db, None, entity="payment", action="payment_cancel",
                          entity_label="Kam dars qaytarishlari bekor qilindi",
                          new_value=len(_lr),
                          note=", ".join(f"{x['name']} {int(x['amount'])}"
                                         for x in _lr[:60]), commit=True)
                print(f"[oylik] kam dars qaytarishlari bekor qilindi: {len(_lr)}")
        except Exception:
            db.rollback()
    # BIR MARTALIK (2026-09-28, Jahongir: "yangi tolov qilganlarga
    # 3-darsgacha qilsa 10 coin berilishi kerak"). Yangi qoida
    # students._pay_coin'da; bu esa sentabrda qoida yo'qligida to'lagan
    # yangi o'quvchilarga coinni to'ldiradi. Idempotent.
    np_key = "np10_backfill_2026-09"
    if not _sd(db, np_key):
        try:
            import students as _stu
            _np = _stu._newpay_backfill(db, date(2026, 9, 1))
            _sm(db, np_key)
            if _np:
                print(f"[coin] yangi o'quvchi +10 to'ldirildi: {len(_np)}")
        except Exception:
            db.rollback()
    # Birinchi yurish 1 so'mlik belgi-to'lovlarga ham coin bergan edi —
    # teskari yozuv bilan qaytariladi (students._newpay_revert_small).
    np_fix = "np10_fix_small_2026-09"
    if not _sd(db, np_fix):
        try:
            import students as _stu2
            _fx = _stu2._newpay_revert_small(db)
            _sm(db, np_fix)
            if _fx:
                print(f"[coin] 1 so'mlik to'lov coini qaytarildi: {len(_fx)}")
        except Exception:
            db.rollback()
    todo = [g for g in _mc_active_groups(db)
            if not _sd(db, f"mcf_{period}_g{g.id}")]
    if not todo and _sd(db, refund_key) and _sd(db, missed_key) \
            and _sd(db, ra_key) and _sd(db, old_key):
        return {"yechildi": 0, "qaytarildi": 0, "tugagan": True}

    pg = False
    try:
        from sqlalchemy import text as _text
        pg = db.get_bind().dialect.name == "postgresql"
        if pg:
            got = db.execute(
                _text("SELECT pg_try_advisory_lock(917202)")).scalar()
            if not got:
                return {"band": True}
    except Exception:
        pg = False

    deadline = _time.monotonic() + max(float(budget_s), 0.0)
    n1 = n2 = 0
    ok1 = ok2 = True
    try:
        if not _sd(db, refund_key):
            try:
                n2, ok2 = _mc_refund_prev(db, today, deadline)
                if ok2:
                    _sm(db, refund_key)
            except Exception:
                db.rollback(); ok2 = False
        try:
            n1, ok1 = _mc_charge_full(db, today, deadline)
        except Exception:
            db.rollback(); ok1 = False
        n3 = 0
        if ok1 and not _sd(db, missed_key):
            try:
                n3 = len(_mc_charge_missed(db, today))
                _sm(db, missed_key)
            except Exception:
                db.rollback()
        # Eski qoida bilan chala yechilganlar — kuniga bir marta
        # (2026-10-02, _mc_fix_old_rule izohiga qarang)
        if ok1 and not _sd(db, old_key):
            try:
                n6 = len(_mc_fix_old_rule(db, today))
                _sm(db, old_key)
                if n6:
                    print(f"[oylik] chala yechilgan to'g'rilandi: {n6}")
            except Exception:
                db.rollback()
        n5 = 0
        if ok1 and not _sd(db, ra_key):
            try:
                n5 = len(_mc_reactivated_after_skip(db, today))
                _sm(db, ra_key)
            except Exception:
                db.rollback()
        if n5:
            print(f"[oylik] qaytib kelganlardan yechildi: {n5} o'quvchi")
        n4 = 0
        if ok1 and not _sd(db, dsc_key):
            try:
                n4 = len(_dsc_fix_month(db, today))
                _sm(db, dsc_key)
            except Exception:
                db.rollback()
        try:
            db.commit()
        except Exception:
            db.rollback()
    finally:
        if pg:
            try:
                from sqlalchemy import text as _text2
                db.execute(_text2("SELECT pg_advisory_unlock(917202)"))
                db.commit()
            except Exception:
                pass
    if n4:
        print(f"[chegirma] shu oy hisobi to'g'rilandi: {n4} o'quvchi")
    return {"yechildi": n1, "qaytarildi": n2, "tutib_qolindi": n3,
            "chegirma_tuzatildi": n4,
            "tugagan": ok1 and ok2}


def _mc_install():
    """common/system modullaridagi eski funksiyani almashtiramiz."""
    import sys as _s
    done = []
    # HAMMA yuklangan modul (2026-10-02). Ilgari faqat common/system/
    # main almashtirilardi. 27-sentabrdagi bo'linishdan keyin login
    # auth_users.py ga ko'chdi ("from common import *" — eski funksiya
    # nusxasi), u almashtirilmay qoldi va 1-oktabr kuni login ESKI
    # qoida bilan "faqat o'tilgan darslar" (1 dars) yechib qo'ydi.
    for mod, m in list(_s.modules.items()):
        if m is None:
            continue
        try:
            old = getattr(m, "_ensure_month_charges", None)
        except Exception:
            continue
        if old is None or not callable(old) \
                or getattr(old, "_mc_new", False):
            continue

        def _wrap(db, _old=old, **kw):
            return _mc_ensure(db, _old, **kw)
        _wrap._mc_new = True
        setattr(m, "_ensure_month_charges", _wrap)
        done.append(mod)
    return done


_MC_INSTALLED = _mc_install()


# =====================================================================
#  IMTIHON HISOBOTI (Analitika -> Imtihonlar tabi)
#  LC UP dagi ko'rinishga o'xshash: tepada 6 ta karta, keyin 4 kesim.
#  O'tish chegarasi: 65% (imtihonda alohida o'tish bali maydoni yo'q).
# =====================================================================
_EXR_PASS = 65.0
_EXR_ROLES = (getattr(roles, "EXAM_VIEW", None)
              or getattr(roles, "ACADEMIC_VIEW", None)
              or roles.FULL_ACCESS)


def _exr_date(v, default=None):
    try:
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return default


def _exr_pct(r, mx):
    """Natijaning foizi: retake bo'lsa u ustun, keyin percent, keyin ball."""
    for v in (getattr(r, "retake_percent", None), r.percent):
        if v is not None:
            return float(v)
    rsc = getattr(r, "retake_score", None)
    sc = rsc if rsc is not None else r.score
    if sc is None or not mx:
        return None
    return float(sc) / float(mx) * 100.0


@app.get("/api/analytics/exam-report")
def exam_report(start: str | None = None, end: str | None = None,
                branch_id: int | None = None, teacher_id: int | None = None,
                limit: int = 300,
                db: Session = Depends(get_db),
                user=Depends(require_role(*_EXR_ROLES))):
    """Imtihonlar bo'yicha umumiy hisobot."""
    d1 = _exr_date(start, date.today().replace(month=1, day=1))
    d2 = _exr_date(end, date.today())
    q = (db.query(models.Exam)
         .filter(models.Exam.date >= d1, models.Exam.date <= d2))
    exams = q.all()
    if not exams:
        return {"pass_mark": _EXR_PASS, "cards": {
            "guruh": 0, "natija": 0, "ortacha": 0, "otgan": 0,
            "yiqilgan": 0, "otish_foizi": 0},
            "groups": [], "students": [], "teachers": [], "failed": []}
    gids = {e.group_id for e in exams if e.group_id}
    groups = {}
    for gid in gids:
        g = db.query(models.Group).filter(models.Group.id == gid).first()
        if g is not None:
            groups[gid] = g
    tnames = {}
    for t in db.query(models.Teacher).all():
        tnames[t.id] = t.full_name
    snames = {}
    for s in db.query(models.Student).all():
        snames[s.id] = s.full_name
    gstat, tstat = {}, {}
    rows, failed = [], []
    tot = pas = 0
    psum = 0.0
    for e in exams:
        g = groups.get(e.group_id)
        if g is None:
            continue
        if branch_id and getattr(g, "branch_id", None) != branch_id:
            continue
        tid = getattr(g, "teacher_id", None)
        if teacher_id and tid != teacher_id:
            continue
        mx = float(e.max_score or 100)
        # O'TISH BALLI (2026-09-10, Jahongir: "test turi boyivha
        # sozlamalarda bir marta"). Har imtihon o'z chegarasini
        # yaratilganda muhrlab oladi. Eski testlarda maydon yo'q —
        # ular avvalgi 65% da qoladi, ya'ni bu hisobotdagi tarixiy
        # raqamlar o'zgarmaydi.
        need = roles.exam_pass_percent(e, roles.LEGACY_EXAM_PASS_REPORT)
        if need is None:      # mock — band bilan baholanadi
            need = roles.LEGACY_EXAM_PASS_REPORT
        for r in (e.results or []):
            if r.absent:
                continue
            pct = _exr_pct(r, mx)
            if pct is None:
                continue
            ok = pct >= need
            tot += 1
            psum += pct
            if ok:
                pas += 1
            gs = gstat.setdefault(e.group_id, {
                "guruh": g.name, "ustoz": tnames.get(tid) or "—",
                "imtihon": set(), "natija": 0, "otgan": 0, "sum": 0.0})
            gs["imtihon"].add(e.id)
            gs["natija"] += 1
            gs["sum"] += pct
            if ok:
                gs["otgan"] += 1
            if tid:
                ts = tstat.setdefault(tid, {
                    "ustoz": tnames.get(tid) or "—", "natija": 0,
                    "otgan": 0, "sum": 0.0, "guruh": set()})
                ts["natija"] += 1
                ts["sum"] += pct
                ts["guruh"].add(e.group_id)
                if ok:
                    ts["otgan"] += 1
            item = {"oquvchi": snames.get(r.student_id) or "—",
                    "guruh": g.name, "imtihon": e.title,
                    "sana": str(e.date), "ball": r.score,
                    "foiz": round(pct, 1), "otdi": ok}
            rows.append(item)
            if not ok:
                failed.append(item)
    rows.sort(key=lambda x: (x["sana"], -x["foiz"]), reverse=True)
    failed.sort(key=lambda x: x["foiz"])
    glist = []
    for gid, v in gstat.items():
        n = v["natija"] or 1
        glist.append({"guruh": v["guruh"], "ustoz": v["ustoz"],
                      "imtihon": len(v["imtihon"]), "natija": v["natija"],
                      "ortacha": round(v["sum"] / n, 1),
                      "otish_foizi": round(v["otgan"] * 100.0 / n, 1)})
    glist.sort(key=lambda x: x["otish_foizi"])
    tlist = []
    for tid, v in tstat.items():
        n = v["natija"] or 1
        tlist.append({"ustoz": v["ustoz"], "guruh": len(v["guruh"]),
                      "natija": v["natija"],
                      "ortacha": round(v["sum"] / n, 1),
                      "otish_foizi": round(v["otgan"] * 100.0 / n, 1)})
    tlist.sort(key=lambda x: -x["otish_foizi"])
    lim = max(20, min(int(limit or 300), 2000))
    # Endi chegara test turiga qarab (Sozlama: Gamification -> Coin
    # qoidasi). Sarlavhada shuni ko'rsatamiz; eski `pass_mark` maydoni
    # o'z joyida qoldi, chunki uni boshqa ekranlar ham o'qishi mumkin.
    _rules = {r.kind: r.percent
              for r in db.query(models.ExamPassRule).all()}
    _labels = " · ".join(
        f"{roles.EXAM_KIND_LABELS.get(k, k)} {_rules.get(k, p):g}%"
        for k, p in roles.DEFAULT_EXAM_PASS.items())
    return {
        "pass_mark": _EXR_PASS,
        "pass_rules": [
            {"kind": k, "label": roles.EXAM_KIND_LABELS.get(k, k),
             "percent": _rules.get(k, p)}
            for k, p in roles.DEFAULT_EXAM_PASS.items()],
        "pass_label": _labels,
        "start": str(d1), "end": str(d2),
        "cards": {
            "guruh": len(gstat),
            "natija": tot,
            "ortacha": round(psum / tot, 1) if tot else 0,
            "otgan": pas,
            "yiqilgan": tot - pas,
            "otish_foizi": round(pas * 100.0 / tot, 1) if tot else 0,
        },
        "groups": glist,
        "teachers": tlist,
        "students": rows[:lim],
        "failed": failed[:lim],
        "jami_natija": tot,
    }


# =====================================================================
#  BUDJET: o'quv yilini tanlash, oyni tasdiqlash (qulf) va avtomat
#  vazifalar.
#   - Tasdiqlash: asoschi yoki moliya direktori.
#   - Qulfni ochish: faqat asoschi.
#   - Har yili 1-iyundan asoschiga vazifa: keyingi o'quv yili budjeti
#     va rejalari 31-avgustgacha to'liq tuzilishi kerak.
#   - Har oyning oxirgi 3 kunida: keyingi oy budjetini tasdiqlash
#     vazifasi (muddat — oyning oxirgi kuni).
# =====================================================================
import calendar as _cal
import re as _re
from datetime import datetime as _dtm

_BUD_APPROVE_ROLES = [roles.FOUNDER, roles.FINANCE_DIRECTOR]
_BUD_UNLOCK_ROLES = [roles.FOUNDER]
_BUD_SRC = "budget"
_BUD_YEAR_TITLE = "Keyingi o'quv yili budjeti va rejalari"
_BUD_MON_TITLE = "Keyingi oy budjetini tasdiqlash"
_BUD_DDL_DONE = {"ok": False}


def _bud_sql(db, q, p=None):
    from sqlalchemy import text as _t
    return db.execute(_t(q), p or {})


def _bud_ddl(db):
    """budget_approvals jadvalini bir marta yaratadi (idempotent)."""
    if _BUD_DDL_DONE["ok"]:
        return
    try:
        name = db.get_bind().dialect.name
    except Exception:
        name = "postgresql"
    pk = ("id INTEGER PRIMARY KEY AUTOINCREMENT" if name == "sqlite"
          else "id SERIAL PRIMARY KEY")
    _bud_sql(db, "CREATE TABLE IF NOT EXISTS budget_approvals ("
                 + pk + ", year INTEGER NOT NULL, month INTEGER NOT NULL, "
                 "approved_by TEXT, approved_at TIMESTAMP, note TEXT)")
    _bud_sql(db, "CREATE UNIQUE INDEX IF NOT EXISTS ix_budget_appr_ym "
                 "ON budget_approvals (year, month)")
    db.commit()
    _BUD_DDL_DONE["ok"] = True


def _bud_iso(v):
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def _bud_approved(db, year):
    """{oy: {"by":..., "at":...}} — shu o'quv yilining tasdiqlangan oylari."""
    _bud_ddl(db)
    rows = _bud_sql(db, "SELECT month, approved_by, approved_at "
                        "FROM budget_approvals WHERE year = :y",
                    {"y": int(year)}).fetchall()
    return {int(r[0]): {"by": r[1], "at": _bud_iso(r[2])} for r in rows}


def _bud_is_locked(db, year, month):
    return int(month) in _bud_approved(db, year)


def _bud_cur_year(today=None):
    t = today or roles.local_today()
    return t.year if t.month >= 9 else t.year - 1


def _bud_ay(year, month):
    """Kalendar oy qaysi o'quv yiliga tegishli."""
    return year if month >= 9 else year - 1


def _bud_filled(db, year):
    """Shu yilda reja kiritilgan oylar soni."""
    rows = db.query(models.BudgetLine.month).filter(
        models.BudgetLine.year == int(year)).distinct().all()
    return len(rows)


def _bud_next_month(today=None):
    t = today or roles.local_today()
    y = t.year + 1 if t.month == 12 else t.year
    m = 1 if t.month == 12 else t.month + 1
    return y, m


def _bud_last_day(y, m):
    return _cal.monthrange(y, m)[1]


@app.get("/api/finance/budget-meta")
def budget_meta(year: int | None = None, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Yil ro'yxati, tasdiqlangan oylar va huquqlar."""
    today = roles.local_today()
    cur = _bud_cur_year(today)
    y = int(year or cur)
    years = []
    for yy in (cur - 1, cur, cur + 1):
        years.append({
            "year": yy,
            "label": roles.plan_year_label(yy),
            "short": f"{yy}-{yy + 1}",
            "is_current": yy == cur,
            "filled": _bud_filled(db, yy),
            "approved": len(_bud_approved(db, yy)),
        })
    ny, nm = _bud_next_month(today)
    nay = _bud_ay(ny, nm)
    due = date(today.year, today.month, _bud_last_day(today.year, today.month))
    return {
        "year": y,
        "year_label": roles.plan_year_label(y),
        "current_year": cur,
        "years": years,
        "filled": _bud_filled(db, y),
        "approved": {str(k): v for k, v in _bud_approved(db, y).items()},
        "can_approve": user.role in tuple(_BUD_APPROVE_ROLES),
        "can_unlock": user.role in tuple(_BUD_UNLOCK_ROLES),
        "can_edit": _has_role(user, roles.BUDGET_EDIT),
        "next": {
            "year": nay,
            "month": nm,
            "label": f"{roles.UZ_MONTHS[nm - 1]} {ny}",
            "approved": _bud_is_locked(db, nay, nm),
            "due": due.isoformat(),
        },
    }


@app.post("/api/finance/budget-approve")
def budget_approve(payload: dict = Body(...), db: Session = Depends(get_db),
                   user=Depends(require_role(*_BUD_APPROVE_ROLES))):
    """Oy budjetini tasdiqlaydi — shundan keyin oy qulflanadi."""
    try:
        y = int(payload.get("year"))
        m = int(payload.get("month"))
    except Exception:
        raise HTTPException(400, "yil va oy kerak")
    if not (1 <= m <= 12):
        raise HTTPException(400, "Oy 1-12 orasida bo'lishi kerak")
    _bud_ddl(db)
    if _bud_is_locked(db, y, m):
        return {"ok": True, "already": True}
    _bud_sql(db, "INSERT INTO budget_approvals "
                 "(year, month, approved_by, approved_at) "
                 "VALUES (:y, :m, :by, :at)",
             {"y": y, "m": m, "by": user.full_name, "at": _dtm.utcnow()})
    db.commit()
    audit.log(db, user, entity="budget", action="approve", entity_id=y,
              entity_label=f"{roles.plan_year_label(y)} · "
                           f"{roles.UZ_MONTHS[m - 1]}",
              new_value="tasdiqlandi", commit=True)
    try:
        _bud_close_month_task(db, y, m)
    except Exception:
        db.rollback()
    return {"ok": True}


@app.delete("/api/finance/budget-approve")
def budget_unapprove(year: int, month: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*_BUD_UNLOCK_ROLES))):
    """Qulfni ochadi — faqat asoschi."""
    _bud_ddl(db)
    _bud_sql(db, "DELETE FROM budget_approvals WHERE year=:y AND month=:m",
             {"y": int(year), "m": int(month)})
    db.commit()
    audit.log(db, user, entity="budget", action="unlock", entity_id=int(year),
              entity_label=f"{roles.plan_year_label(int(year))} · "
                           f"{roles.UZ_MONTHS[int(month) - 1]}",
              new_value="qulf ochildi", commit=True)
    return {"ok": True}


@app.post("/api/finance/budget-copy")
def budget_copy(payload: dict = Body(...), db: Session = Depends(get_db),
                user=Depends(require_role(*roles.BUDGET_EDIT))):
    """Bir o'quv yili budjetini boshqasiga ko'chiradi (+% o'sish bilan).
    Tasdiqlangan oylarga tegmaydi."""
    try:
        to_y = int(payload.get("to_year"))
        from_y = int(payload.get("from_year"))
    except Exception:
        raise HTTPException(400, "to_year va from_year kerak")
    if to_y == from_y:
        raise HTTPException(400, "Bir xil yil tanlangan")
    try:
        growth = float(payload.get("growth_pct") or 0)
    except Exception:
        growth = 0.0
    k = 1.0 + growth / 100.0
    src = db.query(models.BudgetLine).filter(
        models.BudgetLine.year == from_y).all()
    # Hamkor markaz rahbari faqat O'Z markazi qatorlarini ko'chiradi
    if _is_ph(user):
        src = [x for x in src if x.branch_id == user.branch_id]
    if not src:
        raise HTTPException(400, "Tanlangan yilda budjet yo'q")
    locked = set(_bud_approved(db, to_y).keys())
    saved = skipped = 0
    for s in src:
        if s.month in locked:
            skipped += 1
            continue
        amt = round(float(s.amount or 0) * k, 0)
        row = db.query(models.BudgetLine).filter_by(
            year=to_y, month=s.month, kind=s.kind,
            category=s.category, branch_id=s.branch_id).first()
        if row:
            row.amount = amt
        else:
            db.add(models.BudgetLine(
                year=to_y, month=s.month, kind=s.kind, category=s.category,
                branch_id=s.branch_id, amount=amt,
                created_by=user.full_name,
                note=f"{roles.plan_year_label(from_y)}dan ko'chirildi"))
        saved += 1
    db.commit()
    audit.log(db, user, entity="budget", action="copy", entity_id=to_y,
              entity_label=roles.plan_year_label(to_y),
              new_value=f"{roles.plan_year_label(from_y)} +{growth}% · "
                        f"{saved} qator", commit=True)
    try:
        _bud_tasks_ensure(db)
    except Exception:
        db.rollback()
    return {"ok": True, "saved": saved, "skipped": skipped}


# ---- Budjet saqlash: tasdiqlangan oy qulflangan ----
_drop_route("/api/finance/budget/{year}", "PUT")


@app.put("/api/finance/budget/{year}")
def save_budget_locked(year: int, payload: schemas.BudgetSaveIn,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.BUDGET_EDIT))):
    locked = set(_bud_approved(db, year).keys())
    n = 0
    for it in payload.items:
        if it.kind not in ("income", "expense") or not (1 <= it.month <= 12):
            raise HTTPException(400, "Noto'g'ri budjet qatori")
        # Hamkor markaz rahbari (2026-09-17) budjetni faqat O'Z markaziga
        # yozadi — Jony Academy qatorlariga tegolmaydi.
        if _is_ph(user):
            it.branch_id = user.branch_id
        # Budjet filial kesimida kiritiladi (2026-10-02)
        if not it.branch_id and it.kind in ("income", "expense"):
            raise HTTPException(
                400, "Budjet kiritish uchun tepada filialni tanlang")
        if it.month in locked:
            raise HTTPException(
                400, f"{roles.UZ_MONTHS[it.month - 1]} tasdiqlangan — "
                     "avval asoschi qulfni ochishi kerak")
        row = db.query(models.BudgetLine).filter_by(
            year=year, month=it.month, kind=it.kind,
            category=it.category, branch_id=it.branch_id).first()
        if row:
            row.amount = it.amount
        else:
            db.add(models.BudgetLine(
                year=year, month=it.month, kind=it.kind,
                category=it.category, branch_id=it.branch_id,
                amount=it.amount, created_by=user.full_name))
        n += 1
    db.commit()
    audit.log(db, user, entity="budget", action="save", entity_id=year,
              entity_label=roles.plan_year_label(year),
              new_value=f"{n} ta qator", commit=True)
    try:
        _bud_tasks_ensure(db)
    except Exception:
        db.rollback()
    return {"ok": True, "saved": n}


@app.post("/api/finance/budget-assign")
def budget_assign(payload: dict = Body(...), db: Session = Depends(get_db),
                  user=Depends(require_role(roles.FOUNDER))):
    """Filialsiz (umumiy) eski budjet qatorlarini tanlangan filialga
    o'tkazadi. Shu filialda allaqachon bor qator tegilmaydi — umumiy
    qator o'z joyida qoladi."""
    y = int(payload.get("year") or 0)
    bid = int(payload.get("branch_id") or 0)
    if not y or not db.query(models.Branch).get(bid):
        raise HTTPException(400, "Yil va filialni tanlang")
    locked = set(_bud_approved(db, y).keys())
    moved = skipped = 0
    for l in db.query(models.BudgetLine).filter(
            models.BudgetLine.year == y,
            models.BudgetLine.branch_id.is_(None)).all():
        clash = db.query(models.BudgetLine).filter_by(
            year=y, month=l.month, kind=l.kind, category=l.category,
            branch_id=bid).first()
        if clash or l.month in locked:
            skipped += 1
            continue
        l.branch_id = bid
        moved += 1
    db.commit()
    audit.log(db, user, entity="budget", action="assign", entity_id=y,
              entity_label=roles.plan_year_label(y),
              new_value=f"{moved} ta qator filialga o'tkazildi", commit=True)
    return {"ok": True, "moved": moved, "skipped": skipped}


# --------------------------------------------- avtomat vazifalar ----
def _bud_user(db, role):
    q = db.query(models.User).filter(models.User.role == role)
    try:
        q = q.filter(models.User.is_active == True)  # noqa: E712
    except Exception:
        pass
    return q.order_by(models.User.id).first()


def _bud_task_by_key(db, key):
    """Vazifani izohdagi belgi bo'yicha topadi: [bud:...]"""
    return db.query(models.Task).filter(
        models.Task.source == _BUD_SRC,
        models.Task.description.like(f"%[{key}]%")).first()


def _bud_year_ready(db, year):
    """Yil to'liq tuzilgan: har oyda ham daromad, ham xarajat rejasi bor."""
    rows = db.query(models.BudgetLine.month, models.BudgetLine.kind).filter(
        models.BudgetLine.year == int(year)).all()
    inc = {int(m) for m, k in rows if k == "income"}
    exp = {int(m) for m, k in rows if k == "expense"}
    return all(m in inc and m in exp for m in roles.PLAN_MONTHS)


def _bud_close(db, t, why):
    if t and t.status not in tuple(roles.TASK_CLOSED):
        t.status = "done"
        t.done_at = _dtm.utcnow()
        t.result = why
        db.commit()


def _bud_close_month_task(db, ay, m):
    t = _bud_task_by_key(db, f"bud:mon:{ay}-{m:02d}")
    _bud_close(db, t, "Budjet tasdiqlandi")


def _bud_add_source_label():
    try:
        if not any(k == _BUD_SRC for k, _ in roles.TASK_SOURCES):
            roles.TASK_SOURCES.append((_BUD_SRC, "Budjet"))
            roles.TASK_SOURCE_LABELS[_BUD_SRC] = "Budjet"
    except Exception:
        pass


_bud_add_source_label()


def _bud_tasks_ensure(db):
    """Yillik va oylik budjet vazifalarini yaratadi/yopadi. Har login va
    kunlik cron shu funksiyani chaqiradi."""
    today = roles.local_today()
    f = _bud_user(db, roles.FOUNDER)
    if not f:
        return
    fd = _bud_user(db, roles.FINANCE_DIRECTOR)
    watch = fd.id if fd else None

    # ---- 1) Yillik: 1-iyundan 31-avgustgacha ----
    if 6 <= today.month <= 8:
        ty = today.year          # keyingi o'quv yili shu yil sentabrda boshlanadi
        key = f"bud:year:{ty}"
        t = _bud_task_by_key(db, key)
        if _bud_year_ready(db, ty):
            _bud_close(db, t, "Budjet to'liq tuzildi")
        elif t is None:
            db.add(models.Task(
                title=f"{_BUD_YEAR_TITLE} — {roles.plan_year_label(ty)}",
                description=(
                    f"[{key}]\n{roles.plan_year_label(ty)} uchun budjet "
                    "(daromad va xarajat rejasi, 12 oy) va bo'lim rejalari "
                    "to'liq tuzilishi kerak. Muddat — 31-avgust."),
                assignee_id=f.id, watcher_id=watch,
                deadline=date(today.year, 8, 31),
                priority="high", status="new", source=_BUD_SRC,
                created_by="tizim"))
            db.commit()

    # Eski yillik vazifa tugagan bo'lsa — yopamiz
    for t in db.query(models.Task).filter(
            models.Task.source == _BUD_SRC,
            models.Task.description.like("%[bud:year:%")).all():
        if t.status in tuple(roles.TASK_CLOSED):
            continue
        mt = _re.search(r"\[bud:year:(\d{4})\]", t.description or "")
        if mt and _bud_year_ready(db, int(mt.group(1))):
            _bud_close(db, t, "Budjet to'liq tuzildi")

    # ---- 2) Oylik: oyning oxirgi 3 kuni ----
    ny, nm = _bud_next_month(today)
    nay = _bud_ay(ny, nm)
    last = _bud_last_day(today.year, today.month)
    key = f"bud:mon:{nay}-{nm:02d}"
    t = _bud_task_by_key(db, key)
    if _bud_is_locked(db, nay, nm):
        _bud_close(db, t, "Budjet tasdiqlandi")
    elif t is None and today.day >= last - 2:
        db.add(models.Task(
            title=f"{_BUD_MON_TITLE} — {roles.UZ_MONTHS[nm - 1]} {ny}",
            description=(
                f"[{key}]\nMoliya → Budjet bo'limida "
                f"{roles.UZ_MONTHS[nm - 1]} oyi rejasini ko'rib chiqib "
                "tasdiqlang. Tasdiqlangandan keyin oy qulflanadi."),
            assignee_id=f.id, watcher_id=watch,
            deadline=date(today.year, today.month, last),
            priority="high", status="new", source=_BUD_SRC,
            created_by="tizim"))
        db.commit()

    # Tasdiqlangan oylarning ochiq vazifalarini yopamiz
    for t in db.query(models.Task).filter(
            models.Task.source == _BUD_SRC,
            models.Task.description.like("%[bud:mon:%")).all():
        if t.status in tuple(roles.TASK_CLOSED):
            continue
        mt = _re.search(r"\[bud:mon:(\d{4})-(\d{2})\]", t.description or "")
        if mt and _bud_is_locked(db, int(mt.group(1)), int(mt.group(2))):
            _bud_close(db, t, "Budjet tasdiqlandi")


def _bud_install():
    """_ensure_month_charges ustiga qo'shamiz — login va cron ikkalasi ham
    shu funksiyani chaqiradi."""
    import sys as _sys
    done = []
    # Hamma yuklangan modul — _mc_install izohiga qarang (2026-10-02)
    for mod, m in list(_sys.modules.items()):
        if m is None:
            continue
        try:
            old = getattr(m, "_ensure_month_charges", None)
        except Exception:
            continue
        if old is None or not callable(old) \
                or getattr(old, "_bud_new", False):
            continue

        def _wrap(db, _old=old, **kw):
            # budget_s va boshqa argumentlar o'zgarmasdan o'tadi
            # (2026-08-14: oylik hisoblash bosqichma-bosqich bo'ldi).
            r = _old(db, **kw)
            try:
                _bud_tasks_ensure(db)
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
            return r

        _wrap._bud_new = True
        setattr(m, "_ensure_month_charges", _wrap)
        done.append(mod)
    return done


_BUD_INSTALLED = _bud_install()



# ---- Budjet vazifalari: qo'lda ishga tushirish + kunda bir marta o'zi ----
_BUD_RAN = {"day": None}


def _bud_tick(db):
    """Kunda bir marta (har protsessda) vazifalarni tekshiradi."""
    today = roles.local_today()
    if _BUD_RAN["day"] == today.isoformat():
        return
    _BUD_RAN["day"] = today.isoformat()
    try:
        _bud_tasks_ensure(db)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


_drop_route("/api/finance/budget-meta", "GET")


@app.get("/api/finance/budget-meta")
def budget_meta_v2(year: int | None = None, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FINANCE_ACCESS))):
    _bud_tick(db)
    return budget_meta(year=year, db=db, user=user)


@app.post("/api/finance/budget-tasks-run")
def budget_tasks_run(db: Session = Depends(get_db),
                     user=Depends(require_role(roles.FOUNDER))):
    """Budjet vazifalarini shu zahoti tekshiradi (diagnostika uchun ham)."""
    info = {"installed": _BUD_INSTALLED}
    try:
        _bud_tasks_ensure(db)
        info["ok"] = True
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        info["ok"] = False
        info["err"] = f"{type(e).__name__}: {e}"[:400]
    try:
        info["tasks"] = db.query(models.Task).filter(
            models.Task.source == _BUD_SRC).count()
    except Exception:
        db.rollback()
        info["tasks"] = -1
    return info



# Prod'da users.is_active INTEGER — "== True" Postgres'da xato beradi.
# Shuning uchun filtrni Python tomonida bajaramiz.
def _bud_user(db, role):
    rows = db.query(models.User).filter(
        models.User.role == role).order_by(models.User.id).all()
    for u in rows:
        if getattr(u, "is_active", 1) in (True, 1, "1", "true"):
            return u
    return rows[0] if rows else None


# =====================================================================
#  MUZLATISH SANASI + BALANSNI TO'G'RILASH
#
#  Oy boshida to'liq oylik yechiladi (12 dars x 40 000 = 480 000).
#  Agar o'quvchi oy o'rtasida muzlatilsa, muzlatish sanasigacha
#  o'tilgan darslar qayta hisoblanadi va shu oyning hisoblangan
#  to'lovi to'g'rilanadi: 480 000 -> 240 000 (6 dars).
#
#  Qaytib kelganda: o'sha kundan oy oxirigacha qolgan darslar
#  hisoblanib, hisoblangan to'lovga qo'shiladi.
#
#  Qoidalar:
#   - Muzlatish sanasidagi darsning o'zi FAQAT o'quvchi yo'qlamada
#     "keldi" bo'lsa hisoblanadi.
#   - Bitta oyga bitta hisob qatori qoladi — summasi o'zgaradi,
#     eski summa audit jurnaliga yoziladi. Izohda [dars:N] turadi.
#   - 12 darsdan (guruh standartidan) oshmaydi.
# =====================================================================
_FZ_BACK_DAYS = 62          # bundan eski sanaga muzlatib bo'lmaydi


def _fz_period(d) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _fz_date(raw, field: str):
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        raise HTTPException(400, f"{field}: sana noto'g'ri")


def _fz_cap(g) -> int:
    return int(getattr(g, "standard_lessons_per_month", None) or 12)


def _fz_unit(db: Session, s) -> float:
    """Bitta darsning narxi — chegirma hisobga olingan holda."""
    g = s.group
    price = float((getattr(g, "lesson_price", 0) if g else 0) or 0)
    try:
        disc = float(M._student_discount_percent(db, s) or 0)
    except Exception:
        disc = 0.0
    return price * (100.0 - disc) / 100.0


def _fz_row(db: Session, sid: int, period: str):
    return (db.query(models.Payment)
            .filter(models.Payment.student_id == sid,
                    models.Payment.kind == "charge",
                    models.Payment.period == period)
            .order_by(models.Payment.id.desc()).first())


def _fz_lessons_of(db: Session, s, row) -> int:
    """Shu qator nechta dars uchun yozilgan."""
    if row is None:
        return 0
    m = _re.search(r"\[dars:(\d+)\]", row.note or "")
    if m:
        return int(m.group(1))
    unit = _fz_unit(db, s)
    if unit <= 0:
        return 0
    return int(round(abs(float(row.amount or 0)) / unit))


def _fz_held_before(db: Session, s, on: date) -> int:
    """Oy boshidan (yoki qo'shilgan kunidan) `on` sanasigacha o'tilgan
    darslar. `on` kunidagi dars faqat o'quvchi kelgan bo'lsa qo'shiladi.

    2026-08-18, Jahongir: "muzlatishda abdullayeva Muhlisa 5ta dars
    kelgan lekin men muzlatiladigan sanani tanlasam 3ta darsga
    hisoblayabdi nega". Sabab: hisob qo'shilgan sanadan (enrolled_date)
    boshlanardi, lekin o'quvchining undan OLDINGI darslarda ham
    yo'qlamasi bor edi (guruhga keyin rasmiylashtirilgan, darsga esa
    oldinroq kelgan). Yo'qlama - hujjat: belgisi bor dars endi
    qo'shilgan sanadan qat'i nazar HISOBGA KIRADI. Belgisiz darslar
    esa avvalgidek faqat qo'shilgan sanadan keyin hisoblanadi."""
    g = s.group
    if g is None:
        return 0
    month_start = date(on.year, on.month, 1)
    enr = s.enrolled_date if (s.enrolled_date
                              and s.enrolled_date > month_start) \
        else month_start
    try:
        rows = M.billing.held_lessons_query(
            db, g.id, month_start, on).all()
    except Exception:
        return 0
    marked = {a.lesson_id: int(a.present or 0) for a in
              db.query(models.Attendance)
              .filter(models.Attendance.student_id == s.id,
                      models.Attendance.lesson_id.in_(
                          [L.id for L in rows] or [-1])).all()}
    n = 0
    for L in rows:
        if L.date < on:
            # Belgisi bo'lsa — har doim hisobda; belgisiz bo'lsa —
            # faqat qo'shilgan sanadan keyingi darslar
            if L.id in marked or L.date >= enr:
                n += 1
            continue
        # Muzlatish kunining o'zi: faqat kelgan bo'lsa
        if marked.get(L.id) == 1:
            n += 1
    return min(n, _fz_cap(g))


def _fz_left_from(db: Session, s, on: date) -> int:
    """`on` kunidan (shu kun ham kiradi) oy oxirigacha dars kunlari."""
    g = s.group
    if g is None:
        return 0
    try:
        start, end = M.billing.month_bounds(on.year, on.month)
        try:
            M._sync_scheduled_lessons(db, g, start, end)
        except Exception:
            pass
        return len(M._lessons_left_in_month(db, g.id, on))
    except Exception:
        return 0


def _fz_set(db: Session, s, period: str, lessons: int, why: str, user,
            unit: float = None):
    """Shu oyning hisoblangan to'lovini `lessons` dars bo'yicha qo'yadi.
    Yangi qator faqat dars bor bo'lsa yaratiladi.

    `unit` — bitta dars narxi. Muzlatishda u holat o'zgarishidan OLDIN
    hisoblanib beriladi (2026-09-25): aks holda o'quvchi "frozen"
    bo'lgach chegirmasi to'xtab, dars narxi QIMMATLASHIB ketardi va
    muzlatish qarzni kamaytirish o'rniga oshirib yuborardi."""
    lessons = max(int(lessons or 0), 0)
    if unit is None:
        unit = _fz_unit(db, s)
    target = roles.money(lessons * unit)
    row = _fz_row(db, s.id, period)
    gname = s.group.name if s.group else ""
    if row is None:
        if target <= 0:
            return None
        try:
            if M._charge_skipped(db, s.id, period):
                return None
        except Exception:
            pass
        row = models.Payment(
            student_id=s.id, amount=-target, kind="charge",
            note=f"{gname} — {period}: {why}, {lessons} dars [dars:{lessons}]",
            created_by=(user.full_name if user else "avtomat"),
            period=period)
        db.add(row)
        db.flush()
        old = 0.0
    else:
        old = abs(float(row.amount or 0))
        if abs(old - target) < 1:
            return None
        base = _re.sub(r"\s*\[dars:\d+\]", "", row.note or "")
        base = base.split(" · ")[0].strip()
        row.amount = -target
        row.note = f"{base} · {why}: {lessons} dars [dars:{lessons}]"
    audit.log(db, user, entity="payment", action="lessons_recount",
              entity_id=row.id, entity_label=s.full_name, field="amount",
              old_value=f"{old:,.0f}".replace(",", " "),
              new_value=f"{target:,.0f}".replace(",", " "),
              note=why, branch_id=s.branch_id)
    return {"old": old, "new": target, "lessons": lessons}


def _fz_activation_charge(db: Session, s, on: date, user):
    """Faollashtirish to'lovi — deploy'dagi v2 bo'lsa o'shani, bo'lmasa
    asosiy moduldagisini chaqiradi."""
    fn = (globals().get("_charge_from_activation_v3")
          or globals().get("_charge_from_activation_v2"))
    if fn is None:
        fn = getattr(M, "_charge_from_activation", None)
    if fn is None:
        return None
    return fn(db, s, on, user)


# ---- Muzlatish: sana tanlanadi, balans to'g'rilanadi ----
_drop_route("/api/students/{student_id}/freeze", "POST")


@app.post("/api/students/{student_id}/freeze")
def freeze_student_v2(student_id: int, payload: dict = Body(...),
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.FREEZE_ROLES))):
    """O'quvchini muzlatish.

    `from_date` — qaysi kundan muzlatiladi (bo'sh bo'lsa bugundan).
    Shu sanagacha o'tilgan darslar hisoblanib, oyning hisoblangan
    to'lovi to'g'rilanadi. `until` — qachon qaytadi (majburiy)."""
    # FILIAL CHEGARASI (2026-09-06 auditi)
    st = M._get_student_in_scope(db, student_id, user)
    today = roles.local_today()
    until = _fz_date(payload.get("until"), "Qaytish sanasi")
    if until is None:
        raise HTTPException(400, "Qaytish sanasi majburiy")
    if until <= today:
        raise HTTPException(400, "Qaytish sanasi kelajakda bo'lishi kerak")
    frm = _fz_date(payload.get("from_date"), "Muzlatish sanasi") or today
    if frm > today:
        raise HTTPException(400, "Muzlatish sanasi kelajakda bo'lmaydi")
    if (today - frm).days > _FZ_BACK_DAYS:
        raise HTTPException(
            400, f"Muzlatish sanasi {_FZ_BACK_DAYS} kundan eski bo'lmasin")
    note = (payload.get("note") or None)
    # MUZLATISH SABABI ro'yxatdan (2026-08-30, Jahongir: "muzlatish
    # sabablari statistikasi ham kerak"). Noto'g'ri kod kelsa —
    # yozilmaydi, "other" ham emas: statistikaga yolg'on kirmasin.
    rcode = (payload.get("reason") or "").strip()
    if rcode and rcode not in roles.FREEZE_REASON_LABELS:
        raise HTTPException(400, "Muzlatish sababi ro'yxatdan tanlansin")

    # DARS NARXI HOLAT O'ZGARISHIDAN OLDIN (2026-09-25). "frozen"
    # bo'lgach o'quvchining chegirmasi to'xtaydi va narx qimmatlashib
    # ketardi — muzlatish qarzni kamaytirish o'rniga OSHIRIB yuborardi.
    _fz_price = _fz_unit(db, st)
    st.status = "frozen"
    st.frozen_until = until
    st.frozen_reason = rcode or None
    # Izohda sabab nomi ham qolsin — eski ekranlar frozen_note ni
    # o'qiydi, ular uchun hech narsa o'zgarmasin.
    lbl = roles.FREEZE_REASON_LABELS.get(rcode)
    st.frozen_note = (f"{lbl} — {note}" if (lbl and note)
                      else (lbl or note))
    note = st.frozen_note
    try:
        M._freeze_task(db, st, until, note)
    except Exception:
        pass
    audit.log(db, user, entity="student", action="freeze",
              entity_id=st.id, entity_label=st.full_name,
              new_value=f"{frm.isoformat()} dan, qaytishi: "
                        f"{until.isoformat()}",
              note=note, branch_id=st.branch_id)
    db.commit()

    adjust = None
    if st.group_id and st.group is not None:
        # ORQAGA SANA BILAN MUZLATISH (2026-09-25). Ilgari faqat
        # muzlatish sanasi TUSHGAN OY to'g'rilanardi. 62 kungacha
        # orqaga ruxsat berilgani uchun, masalan 20-avgustdan
        # muzlatilsa, sentabr hisobi to'liq summada qolib ketardi.
        # Endi muzlatish oyidan bugungi oygacha hammasi ko'riladi:
        #   - muzlatish oyi — o'sha sanagacha o'tilgan darslar;
        #   - keyingi oylar — o'quvchi ro'yxatga tushgan darslar
        #     (odatda 0, shunda qator nolga tushadi; agar baribir
        #     kelgan bo'lsa, o'sha darslar hisoblanadi).
        why = f"{frm.strftime('%d.%m')} dan muzlatildi"
        y, m = frm.year, frm.month
        first = True
        while (y, m) <= (today.year, today.month):
            on = date(y, m, 1)
            n = _fz_held_before(db, st, frm) if first else \
                _af_marked_lessons(db, st, on)
            res = _fz_set(db, st, f"{y:04d}-{m:02d}", n, why, user,
                          unit=_fz_price)
            if first:
                adjust = res
                first = False
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        db.commit()
    return {"ok": True, "from_date": frm.isoformat(), "adjust": adjust}


@app.get("/api/students/{student_id}/freeze-preview")
def freeze_preview(student_id: int, from_date: str | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Muzlatishdan oldin: nechta dars hisoblanadi va summa qanday
    o'zgaradi."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    frm = _fz_date(from_date, "Muzlatish sanasi") or roles.local_today()
    period = _fz_period(frm)
    row = _fz_row(db, st.id, period)
    n = _fz_held_before(db, st, frm) if st.group_id else 0
    unit = _fz_unit(db, st)
    return {
        "from_date": frm.isoformat(),
        "period": period,
        "lessons": n,
        "unit": roles.money(unit),
        "current": roles.money(abs(float(row.amount or 0))) if row else 0,
        "target": roles.money(n * unit),
        "has_charge": row is not None,
    }


# ---- Qayta faollashtirish: qolgan darslar qo'shiladi ----
_drop_route("/api/students/{student_id}/activate", "POST")


@app.post("/api/students/{student_id}/activate")
def activate_student_v3(student_id: int, payload: dict | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Sinovdagi yoki muzlatilgan o'quvchini faol qiladi.

    Muzlatilgan o'quvchi qaytganda: shu kundan oy oxirigacha qolgan
    darslar hisoblanib, oyning hisoblangan to'loviga qo'shiladi."""
    # FILIAL CHEGARASI (2026-09-06 auditi)
    s = M._get_student_in_scope(db, student_id, user)
    if s.status == "active":
        raise HTTPException(400, "Bu o'quvchi allaqachon faol")

    today = roles.local_today()
    on = _fz_date((payload or {}).get("on"), "Sana") or today
    if on > today:
        raise HTTPException(400, "Kelajakdagi sanani tanlab bo'lmaydi")

    # GURUHSIZ FAOLLASHTIRISH TAQIQI (2026-10-05, Jahongir: "Gayratova
    # Nargiza, Rahmonova Diyora, Maqsudova Durdona o'zidan o'zi arxivga
    # o'tib qolibdi, nega"). Sabab: sinovda 2 marta kelmagani uchun
    # guruhdan avtomat chiqarilgan o'quvchi arxivdan GURUHSIZ faol
    # qilindi; tizim "guruhsiz odam faol bo'la olmaydi" qoidasi bilan
    # uni bir daqiqada "Chiqib ketgan"ga, so'ng qarzsiz bo'lgani uchun
    # arxivga qaytardi. Endi guruh shu yerda tanlanadi (group_id),
    # tanlanmasa — tushunarli xato, jimgina arxivga qaytish yo'q.
    gid = (payload or {}).get("group_id")
    if gid:
        g = db.query(models.Group).get(int(gid))
        if g is None:
            raise HTTPException(404, "Guruh topilmadi")
        _CM.attach_group(db, s, g.id, user, joined=on,
                       note="Faollashtirishda guruhga qo'shildi")
        db.flush()
    if not s.group_id:
        # Bog'lanish ochiq qolgan bo'lsa — asosiy guruh undan olinadi
        _CM.sync_primary_group(db, s)
    if not s.group_id:
        raise HTTPException(
            400, "O'quvchi hech qaysi guruhda emas. Avval guruhga qo'shing "
                 "(yoki guruh sahifasidagi \"Guruhdan o'chirilganlar\" "
                 "ro'yxatidan \"Qaytarish\" tugmasini bosing) — guruhsiz "
                 "faol o'quvchini tizim avtomat arxivga qaytaradi.")

    old_status = s.status
    s.archive_when_paid = 0
    s.status = "active"
    if not s.enrolled_date or s.enrolled_date > on:
        s.enrolled_date = on
    s.frozen_until = None
    try:
        M._sync_student_left_date(s)
    except Exception:
        pass

    db.flush()  # Family count must include this newly active child.
    charge = adjust = None
    try:
        charge = _fz_activation_charge(db, s, on, user)
    except Exception:
        charge = None
    if charge is None and old_status == "frozen" and s.group_id \
            and s.group is not None:
        period = _fz_period(on)
        row = _fz_row(db, s.id, period)
        if row is not None:
            have = _fz_lessons_of(db, s, row)
            left = _fz_left_from(db, s, on)
            total = min(have + left, _fz_cap(s.group))
            if left > 0:
                adjust = _fz_set(db, s, period, total,
                                 f"{on.strftime('%d.%m')} dan qaytdi", user)

    from common import _refresh_family_charges
    _refresh_family_charges(db, s)

    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old_status, new_value="active",
              branch_id=s.branch_id,
              note=(f"{on.isoformat()} dan — {charge['lessons']} dars"
                    if charge else on.isoformat()))
    db.commit()
    return {"ok": True, "status": s.status, "activated_on": on.isoformat(),
            "charge": charge, "adjust": adjust}


# ---- Guruhga qaytarish (2026-10-05) ----
@app.post("/api/groups/{group_id}/students/{student_id}/return")
def return_to_group(group_id: int, student_id: int,
                    payload: dict | None = None,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.STUDENT_RESTORE))):
    """"Guruhdan o'chirilganlar" ro'yxatidagi o'quvchini shu guruhga
    qaytaradi (Jahongir: "guruh arxivida turgan o'quvchini ism familya
    yonida guruhga qaytarish tugmasi tursin, guruhga qaytarganda avtomat
    oylik tanlagan kundan boshlab oy oxirigacha hisoblanishi kerak").

    Bog'lanish qayta ochiladi, o'quvchi faol bo'ladi va tanlangan
    kundan oy oxirigacha bo'lgan darslar uchun hisob yoziladi
    (oddiy faollashtirish qoidasi bilan bir xil). Hech narsa
    o'chirilmaydi."""
    s = M._get_student_in_scope(db, student_id, user)
    g = db.query(models.Group).get(group_id)
    if g is None:
        raise HTTPException(404, "Guruh topilmadi")
    inb = getattr(M, "_in_user_branches", None)
    if inb is not None and not inb(db, user, g.branch_id, null_ok=True):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")
    today = roles.local_today()
    on = _fz_date((payload or {}).get("on"), "Sana") or today
    if on > today:
        raise HTTPException(400, "Kelajakdagi sanani tanlab bo'lmaydi")
    in_now = g.id in _CM.student_group_ids(db, s.id) or s.group_id == g.id
    if in_now and s.status in ("active", "trial", "frozen"):
        raise HTTPException(400, "O'quvchi allaqachon shu guruhda")

    _CM.attach_group(db, s, g.id, user, joined=on, note="Guruhga qaytarildi")
    s.archive_when_paid = 0
    db.flush()
    if s.status == "active":
        # Boshqa guruhda faol o'qiyapti — faqat shu guruhga qaytariladi,
        # asosiy oylik o'sha guruh bo'yicha allaqachon yozilgan.
        audit.log(db, user, entity="student", action="return_group",
                  entity_id=s.id, entity_label=s.full_name,
                  field="group", new_value=g.name, branch_id=s.branch_id,
                  note=f"{on.isoformat()} dan guruhga qaytarildi")
        db.commit()
        return {"ok": True, "status": s.status, "group": g.name,
                "charge": None, "activated_on": on.isoformat()}
    res = activate_student_v3(student_id, {"on": on.isoformat()}, db, user)
    audit.log(db, user, entity="student", action="return_group",
              entity_id=s.id, entity_label=s.full_name, field="group",
              new_value=g.name, branch_id=s.branch_id,
              note=f"{on.isoformat()} dan guruhga qaytarildi", commit=True)
    return {**res, "group": g.name}


# =====================================================================
#  AVTOMUZLATISHDA OY TO'LOVINI QAYTA HISOBLASH
#
#  Ketma-ket 3 darsga kelmagan o'quvchi avtomat muzlatiladi va o'sha
#  3 ta yo'qlama bekor qilinadi (ustoz oyligidan ham chiqadi). Ammo oy
#  boshida undan to'liq oylik yechib olingan bo'ladi — hisoblangan
#  qator 480 000 bo'lib qolaverardi va uni har safar qo'lda
#  to'g'rilashga to'g'ri kelardi.
#
#  Endi bu ish avtomat: muzlatilgan zahoti shu oyning hisoblangan
#  to'lovi ro'yxatga tushgan (bekor qilinmagan) darslar soni bo'yicha
#  qayta yoziladi.
#
#      6 dars o'tdi -> 3 ta kelmadi -> avtomuzlatildi
#      480 000  ->  240 000
#
#  Qoidalar:
#    * Muzlatishga sabab bo'lgan 3 ta dars hisobga kirmaydi — ular
#      allaqachon o'chirilgan.
#    * Undan oldingi darslar (kelgan ham, qoldirgan ham) hisoblanadi —
#      markazning qoidasi shu: kelmagani uchun pul qaytmaydi.
#    * Summa faqat KAMAYADI. Qator allaqachon kamaytirilgan bo'lsa
#      (qo'lda yoki muzlatish orqali) qayta ko'tarilmaydi.
#    * Eski oylarga tegilmaydi — faqat muzlatilgan kun oyidagi qator.
#    * Qaytib faollashtirilganda oyning qolgan darslari alohida
#      yechiladi (activate_student_v3) — bu ish o'zgarmaydi.
# =====================================================================
_AF_WHY = "avtomuzlatish"


def _af_marked_lessons(db: Session, s, on: date) -> int:
    """`on` sanasi oyida o'quvchi ro'yxatiga tushgan darslar soni.

    Avtomuzlatish bekor qilgan 3 ta yo'qlama bu paytda allaqachon
    o'chirilgan, shuning uchun ular bu yerga kirmaydi."""
    g = s.group
    if g is None:
        return 0
    try:
        start, end = M.billing.month_bounds(on.year, on.month)
    except Exception:
        return 0
    if s.enrolled_date and s.enrolled_date > start:
        start = s.enrolled_date
    if start > end:
        return 0
    try:
        n = (db.query(models.Attendance)
             .join(models.Lesson,
                   models.Lesson.id == models.Attendance.lesson_id)
             .filter(models.Attendance.student_id == s.id,
                     models.Lesson.group_id == g.id,
                     models.Lesson.held == 1,
                     models.Lesson.date >= start,
                     models.Lesson.date <= end)
             .count())
    except Exception:
        return 0
    return min(int(n or 0), _fz_cap(g))


def _af_recount(db: Session, s):
    """Avtomuzlatilgan o'quvchining shu oylik hisobini to'g'rilaydi."""
    if s is None or s.group_id is None or s.group is None:
        return None
    today = roles.local_today()
    period = _fz_period(today)
    row = _fz_row(db, s.id, period)
    if row is None:
        # Bu oy uchun hech narsa yechilmagan — to'g'rilaydigan narsa yo'q.
        return None
    n = _af_marked_lessons(db, s, today)
    if n >= _fz_lessons_of(db, s, row):
        # Kamaymaydi — ortiqcha yozuv va audit qoldirmaymiz.
        return None
    return _fz_set(db, s, period, n, _AF_WHY, None)


def _af_install():
    """`_freeze_task` ustiga qo'shamiz — avtomuzlatish shu funksiyani
    chaqiradi (qo'lda muzlatishda `until` doim to'ldirilgan bo'ladi,
    shuning uchun ikkalasi aralashib ketmaydi)."""
    import sys as _s
    done = []
    # 2026-09-25 TUZATISH (Jahongir: "muzlatilgan oquvchida katta
    # qarzdorlik qolib ketyabdi"). Ilgari bu yerda faqat uchta modul
    # nomi yozilgan edi: "common", "system", "main". Avtomuzlatishning
    # YAGONA chaqiruv joyi esa groups_lessons.py — u `from common
    # import *` orqali funksiyaning ESKI nusxasini ushlab turardi.
    # Natijada "480 000 -> 240 000" qayta hisobi jonli tizimda hech
    # qachon ishlamagan: 3 darsga kelmagani uchun avtomuzlatilgan
    # o'quvchida oy boshidagi to'liq summa qarz bo'lib qolaverardi.
    # Endi `_tr_install` dagi kabi nomni ushlab turgan HAMMA modul
    # yamaladi.
    for mod, m in list(_s.modules.items()):
        if m is None:
            continue
        try:
            old = getattr(m, "_freeze_task", None)
        except Exception:
            continue
        if old is None or getattr(old, "_af_new", False):
            continue

        def _wrap(db, st, until, note, _old=old):
            res = _old(db, st, until, note)
            try:
                if until is None and "avtomuzlat" in (note or "").lower():
                    _af_recount(db, st)
            except Exception:
                pass
            return res

        _wrap._af_new = True
        setattr(m, "_freeze_task", _wrap)
        done.append(mod)
    return done


_AF_INSTALLED = _af_install()


# =====================================================================
#  GURUH ALMASHTIRISHDA OYLIK CHEGARA
#
#  Bir oyda o'quvchidan STANDART dars sonidan (odatda 12 ta) ortiq pul
#  olinmaydi — 13- va 14-darslar bepul. Guruhdan guruhga o'tganda esa
#  eski guruhdagi darslar bilan yangi guruhdagi qolgan darslar oddiy
#  qo'shilib ketardi:
#
#      6 dars (eski guruh) + 8 dars (yangi guruh) = 14 dars
#      560 000 so'm  ->  480 000 dan oshib ketdi
#
#  Endi jami dars soni oy standartida cheklanadi: avval eski
#  guruhdagi o'tilgan darslar, qolgan joyga yangi guruh darslari
#  yoziladi. Ortiqchasi bepul va izohda ko'rinib turadi.
# =====================================================================
def _tr_cap(new_g, old_gs) -> int:
    """Oyning standart dars soni — yangi guruhniki asos."""
    for g in [new_g] + list(old_gs or []):
        n = getattr(g, "standard_lessons_per_month", None) if g else None
        if n:
            return int(n)
    return 12


def _tr_old_rows(db: Session, s, new_g, month_start, today):
    """Shu oy eski guruh(lar)da belgilangan yo'qlamalar — guruhlar
    kesimida, birinchi dars sanasi bo'yicha tartiblangan."""
    try:
        rows = (db.query(models.Lesson.group_id, models.Lesson.date)
                .join(models.Attendance,
                      models.Attendance.lesson_id == models.Lesson.id)
                .filter(models.Attendance.student_id == s.id,
                        models.Lesson.date >= month_start,
                        models.Lesson.date <= today,
                        models.Lesson.group_id != new_g.id)
                .order_by(models.Lesson.date).all())
    except Exception:
        return []
    order, cnt = [], {}
    for gid, _d in rows:
        if gid not in cnt:
            order.append(gid)
            cnt[gid] = 0
        cnt[gid] += 1
    return [(gid, cnt[gid]) for gid in order]


def _transfer_recharge_v2(db: Session, s, old_g, new_g, user, today=None):
    """Guruh almashtirishda joriy oy to'lovini qayta taqsimlaydi.

    Eski guruhda o'tilgan darslar o'sha guruh narxida, yangi guruhda
    bugundan oy oxirigacha qolgan darslar yangi narxda. JAMI dars soni
    oy standartidan (12) oshmaydi — ortig'i bepul.

    Qaytaradi: eski guruhdagi belgilangan yo'qlamalar soni."""
    today = today or roles.local_today()
    period = f"{today.year:04d}-{today.month:02d}"
    month_start = date(today.year, today.month, 1)

    rows = _tr_old_rows(db, s, new_g, month_start, today)
    gmap = {}
    if rows:
        gmap = {g.id: g for g in db.query(models.Group).filter(
            models.Group.id.in_([gid for gid, _ in rows])).all()}
    cap = _tr_cap(new_g, list(gmap.values()))

    room = cap
    old_attended = 0
    old_sum = 0.0
    billed = 0
    parts = []
    for gid, cnt in rows:
        g = gmap.get(gid)
        price = float((g.lesson_price or 0) if g else 0)
        take = min(int(cnt), max(room, 0))
        old_sum += take * price
        old_attended += int(cnt)
        billed += take
        room -= take
        if g:
            parts.append(f"{g.name}da {cnt} dars")

    try:
        new_cnt = len(M._lessons_left_in_month(db, new_g.id, today))
    except Exception:
        new_cnt = 0
    new_take = min(int(new_cnt), max(room, 0))
    new_sum = new_take * float(new_g.lesson_price or 0)
    billed += new_take
    parts.append(f"{new_g.name}da {new_cnt} dars")

    try:
        disc = float(M._student_discount_percent(db, s) or 0)
    except Exception:
        disc = 0.0
    total = roles.money((old_sum + new_sum) * (100.0 - disc) / 100.0)

    free = (old_attended + new_cnt) - billed
    note = "Guruh almashtirildi: " + " + ".join(parts)
    if free > 0:
        note += f" — {billed} dars hisoblandi, {free} dars bepul"
    if disc:
        note += f" (chegirma {disc:g}%)"

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
    elif total > 0 and not M._charge_skipped(db, s.id, period):
        p = models.Payment(student_id=s.id, amount=-abs(total),
                           kind="charge", period=period, note=note,
                           created_by=(user.full_name if user else "avtomat"))
        db.add(p)
        audit.log(db, user, entity="payment", action="create",
                  entity_label=s.full_name,
                  field="Oylik hisob (guruh almashtirildi)",
                  new_value=p.amount, note=note, branch_id=s.branch_id)
    return old_attended


def _tr_install():
    """`_transfer_recharge` ni qaysi modulda bo'lsa o'sha yerda
    almashtiramiz — guruh ko'chirish endpointi shu nomni chaqiradi."""
    import sys as _s
    done = []
    for name, m in list(_s.modules.items()):
        if m is None:
            continue
        try:
            fn = getattr(m, "_transfer_recharge", None)
        except Exception:
            continue
        if fn is None or getattr(fn, "_tr_new", False):
            continue
        _transfer_recharge_v2._tr_new = True
        setattr(m, "_transfer_recharge", _transfer_recharge_v2)
        done.append(name)
    return done


_TR_INSTALLED = _tr_install()


# =====================================================================
#  NOMZOD ZAXIRASI (talent pool)
#
#  Yaxshi nomzod bor, lekin hozir o'rin yo'q yoki maosh kelishilmadi —
#  uni "Rad etildi" ga tashlab yuborsak, olti oydan keyin o'rin
#  ochilganda uni hech kim eslamaydi. Endi alohida bosqich bor:
#  "Zaxiraga olindi". Nomzodlar ro'yxatidan shu bosqichni tanlab
#  zaxirada kimlar borligini ko'rish mumkin.
#
#  Voronkaga kirmaydi — zaxira yutuq ham, yo'qotish ham emas, u
#  kelajakdagi imkoniyat.
# =====================================================================
_POOL_KEY = "pool"
_POOL_LABEL = "Zaxiraga olindi"


def _pool_install():
    """roles moduliga yangi bosqichni qo'shamiz (import paytida)."""
    try:
        stages = getattr(roles, "CANDIDATE_STAGES", None)
        if stages is None:
            return False
        if any(k == _POOL_KEY for k, _l in stages):
            return "bor"
        stages.append((_POOL_KEY, _POOL_LABEL))
        labels = getattr(roles, "CANDIDATE_STAGE_LABELS", None)
        if isinstance(labels, dict):
            labels[_POOL_KEY] = _POOL_LABEL
        # Voronka: zaxira ham, rad etilgan ham bosqich emas.
        roles.CANDIDATE_FUNNEL = [
            k for k, _l in stages if k not in ("rejected", _POOL_KEY)]
        return True
    except Exception:
        return False


_POOL_INSTALLED = _pool_install()


# =====================================================================
#  RAHBAR O'Z GURUHIGA YO'QLAMA QO'YMAYDI
#
#  O'quv bo'limi rahbari va filial rahbari ba'zan o'zlari ham dars
#  beradi. Muammo shundaki, ular rahbar sifatida o'tgan kun
#  yo'qlamasini ham o'zgartira oladi (PAST_ATTENDANCE) — ya'ni o'z
#  oyligini o'zi yozib qo'ya oladi. Yo'qlama — pul hujjati, shuning
#  uchun bir odam ham o'qituvchi, ham nazoratchi bo'lib qolmasligi
#  kerak.
#
#  Endi: rahbar LAVOZIMIDA turib o'zi ustoz bo'lgan guruhda
#  yo'qlama, baho va dars ko'chirish yopiq. Lavozimi "ustoz" ga
#  o'zgartirilsa — hammasi ochiladi (o'shanda filial almashtirgich
#  yo'qoladi, chunki ustoz faqat o'z filialini ko'radi).
#
#  Boshqa ustozlarning guruhlarida rahbarning huquqi o'zgarmaydi.
# =====================================================================
_OWN_LOCK_ROLES = [roles.ACADEMIC_HEAD, roles.BRANCH_MANAGER]
_OWN_LOCK_MSG = ("Bu — o'zingiz dars beradigan guruh. Rahbar lavozimida "
                 "o'z guruhingizga yo'qlama/baho qo'yilmaydi. Buni ustoz "
                 "lavozimida bajarasiz.")


def _own_teacher(db: Session, user):
    """Foydalanuvchining ustoz yozuvi (bo'lsa)."""
    try:
        return M._teacher_of_user(db, user)
    except Exception:
        return None


def _own_locked(db: Session, user, group_id) -> bool:
    """Shu guruh — foydalanuvchining o'z guruhimi va u rahbarmi?"""
    if user is None or not group_id:
        return False
    if getattr(user, "role", None) not in _OWN_LOCK_ROLES:
        return False
    t = _own_teacher(db, user)
    if t is None:
        return False
    g = (db.query(models.Group)
         .filter(models.Group.id == int(group_id)).first())
    return bool(g is not None and g.teacher_id == t.id)


def _own_locked_lesson(db: Session, user, lesson_id) -> bool:
    if not lesson_id:
        return False
    L = (db.query(models.Lesson)
         .filter(models.Lesson.id == int(lesson_id)).first())
    return bool(L is not None and _own_locked(db, user, L.group_id))


def _own_guard(kw, kind: str):
    """Yozishdan oldingi tekshiruv. Sessiya va foydalanuvchi endpoint
    argumentlaridan olinadi."""
    db = kw.get("db")
    user = kw.get("user")
    if db is None or user is None:
        return
    gid = kw.get("gid") or kw.get("group_id")
    lid = kw.get("lesson_id")
    if kind == "lesson":
        bad = _own_locked_lesson(db, user, lid)
    elif kind == "payload_group":
        p = kw.get("payload")
        bad = _own_locked(db, user, getattr(p, "group_id", None))
    else:
        bad = _own_locked(db, user, gid)
    if bad:
        raise HTTPException(403, _OWN_LOCK_MSG)


def _own_wrap(path: str, method: str, kind: str):
    """Mavjud endpointni o'rab olamiz — kodini qayta yozmaymiz."""
    import functools as _ft
    for r in app.routes:
        if getattr(r, "path", None) != path:
            continue
        if method not in (getattr(r, "methods", None) or ()):
            continue
        orig = getattr(getattr(r, "dependant", None), "call", None)
        if orig is None or getattr(orig, "_own_new", False):
            continue

        @_ft.wraps(orig)
        def _new(*a, _o=orig, _k=kind, **kw):
            _own_guard(kw, _k)
            return _o(*a, **kw)

        _new._own_new = True
        r.dependant.call = _new
        try:
            r.endpoint = _new
        except Exception:
            pass
        return True
    return False


def _own_install():
    done = {}
    for path, method, kind in (
        ("/api/lessons/{lesson_id}/attendance", "PUT", "lesson"),
        ("/api/lessons/{lesson_id}/grades", "PUT", "lesson"),
        ("/api/lessons/{lesson_id}/homework", "PUT", "lesson"),
        ("/api/groups/{gid}/reschedule", "POST", "group"),
        ("/api/me/reschedules", "POST", "payload_group"),
    ):
        done[f"{method} {path}"] = _own_wrap(path, method, kind)
    return done


_OWN_INSTALLED = _own_install()


@app.get("/api/groups/{gid}/my-access")
def group_my_access(gid: int, db: Session = Depends(get_db),
                    user=Depends(M.get_current_user)):
    """Shu guruhda men yo'qlama/baho qo'ya olamanmi.

    Frontend jurnalni shu javobga qarab yopadi — ochiladi, lekin
    katakchalar o'chirilgan bo'ladi va sabab yozib turadi."""
    locked = _own_locked(db, user, gid)
    # "Bu guruh MENIKI" — ustoz o'z guruhining nomi, darajasi, vaqti
    # va xonasini tahrirlashi uchun (2026-09-01, Jahongir). Frontend
    # foydalanuvchining teacher_id sini bilmaydi, shuning uchun
    # javobni server beradi. Qo'shimcha so'rov yo'q: bu manzil guruh
    # sahifasi ochilganda allaqachon chaqiriladi.
    own_group = False
    _t = db.query(models.Teacher).filter(
        models.Teacher.user_id == getattr(user, "id", None)).first()
    if _t:
        _g = db.query(models.Group).get(gid)
        own_group = bool(_g and _g.teacher_id == _t.id)
    return {
        "group_id": gid,
        "locked": locked,
        "can_mark": (not locked) and (
            getattr(user, "role", None) in tuple(roles.TEACHING_STAFF)),
        "reason": _OWN_LOCK_MSG if locked else None,
        "own_group": own_group,
    }


# ---------------------------------------------------------------------------
# IKKI GURUHDA O'QIYDIGAN BOLA GURUH ICHIDA HAM KO'RINSIN  (_MGX_*)
#
# Jahongir: "2 ta guruhda bor, ikkalasidayam faol ko'rsatyapti, lekin
# guruhga kirsa muzlatilgan chiqyapti."
#
# Sabab. Ko'p guruh uchun student_groups jadvali qo'shildi, lekin guruh
# ichidagi ro'yxatni beradigan yagona yordamchi — _group_students —
# hamon eski qoidada ishlayotgan edi:
#
#     Student.group_id == group_id
#
# Student.group_id esa BITTA: u ASOSIY guruhni ko'rsatadi. Munisaning
# asosiy guruhi "Rus tili", shuning uchun "New" guruhining ro'yxatiga
# u umuman tushmagan. Lekin uning shu guruhda yo'qlamasi bor edi —
# davomat jadvali esa "ro'yxatda yo'q, ammo belgisi bor" degan bolani
# BOSHQA GURUHGA O'TGAN deb hisoblaydi (bu qoida haqiqiy ko'chirish
# uchun yozilgan). Natijada ikkinchi guruhda u kulrang, faqat o'qish
# uchun qator bo'lib turdi.
#
# Tuzatish: _group_students endi ikkala manbani ham o'qiydi —
# Student.group_id VA student_groups dagi faol bog'lanish. Bitta
# yordamchi 30 dan ortiq joyda ishlatiladi (ro'yxat, davomat, baho,
# imtihon, uy vazifasi), shuning uchun bitta joyni tuzatish hammasini
# tuzatadi.
#
# Nega modullarni aylanib chiqamiz. Modullar `from common import *`
# yozadi — ya'ni har biri funksiyaning O'Z nusxasini ushlab turadi.
# Faqat common dagisini almashtirsak, ular eskisini chaqiraverardi.
# ---------------------------------------------------------------------------

_MGX_LINK = getattr(models, "StudentGroupLink", None)


def _mgx_group_students(db: Session, group_id: int):
    """Guruh ro'yxati: asosiy guruhi shu bo'lganlar + shu guruhga
    bog'langanlar (ikkinchi, uchinchi fan)."""
    ids = set()
    if _MGX_LINK is not None:
        try:
            for (sid,) in (db.query(_MGX_LINK.student_id)
                           .filter(_MGX_LINK.group_id == group_id,
                                   _MGX_LINK.active == 1).all()):
                ids.add(int(sid))
        except Exception:
            ids = set()
    q = db.query(models.Student)
    if ids:
        q = q.filter((models.Student.group_id == group_id) |
                     (models.Student.id.in_(list(ids))))
    else:
        q = q.filter(models.Student.group_id == group_id)
    return q.order_by(models.Student.full_name).all()


def _mgx_install() -> int:
    """Yordamchini yuklangan hamma modulda almashtiradi."""
    n = 0
    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        try:
            cur = getattr(mod, "_group_students", None)
        except Exception:
            continue
        if cur is not None and cur is not _mgx_group_students:
            try:
                setattr(mod, "_group_students", _mgx_group_students)
                n += 1
            except Exception:
                pass
    return n


_MGX_PATCHED = _mgx_install()


# --- O'quvchi kartasidagi "Holati" haqiqiy bo'lsin ---
#
# Karta har ikki guruh uchun ham qotirilgan "Faol" yozib turardi.
# Muzlatilgan bola ham, guruhdan chiqarilgan bola ham "Faol"
# ko'rinardi — bu ekranga ishonchni yo'qotadi.
_MGX_LABEL = {
    "active": "Faol",
    "frozen": "Muzlatilgan",
    "archived": "Arxivda",
    "left": "Chiqib ketgan",
    "trial": "Sinov darsi",
}

_mgx_groups_v1 = _find_endpoint("/api/students/{student_id}/groups", "GET")

if _mgx_groups_v1 is not None:
    _drop_route("/api/students/{student_id}/groups", "GET")

    @app.get("/api/students/{student_id}/groups")
    def mgx_student_groups(student_id: int, db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *roles.STUDENT_GROUPS_VIEW))):
        rows = _mgx_groups_v1(student_id=student_id, db=db, user=user)
        s = db.query(models.Student).get(student_id)
        st = getattr(s, "status", None) or "active"
        seq = rows if isinstance(rows, list) else (rows or {}).get("rows") or []
        for r in seq:
            if not isinstance(r, dict):
                continue
            if not r.get("active"):
                # Bog'lanish yopilgan — bola shu guruhda o'qimaydi
                r["status"] = "left"
                r["status_label"] = "Guruhdan chiqarilgan"
            else:
                r["status"] = st
                r["status_label"] = _MGX_LABEL.get(st, st)
        return rows


# Ikki guruh tuzatishi jonli holatga chiqarildi (2026-08-18).


# =====================================================================
#  SHAXSIY RIVOJLANISH  (_PD_*)
#
#  Ustozlar uchun video kutubxonasi. Uch narsa muhim:
#
#  1) Ko'rgani rostdan o'lchansin. Ustoz "ko'rdim" deb belgilamaydi —
#     pleyer har necha soniyada "hozir nechanchi soniyadaman" deb
#     xabar beradi, server esa videoni 10 soniyalik bo'laklarga bo'lib,
#     qaysi bo'lak ko'rilganini belgilab boradi. Shuning uchun oxiriga
#     tashlab yuborish foizni oshirmaydi: oradagi bo'laklar bo'sh qoladi.
#
#  2) Statistika faqat asoschi va HR menejerga ko'rinadi. Ustoz o'z
#     foizini ko'radi, boshqalarnikini ko'rmaydi.
#
#  3) Video havolasi ochiq turmaydi: ustozga faqat YouTube ID beriladi
#     va u JonyOS ichida ochiladi. Ustoz YouTube saytining o'zida
#     ko'rsa — foiz o'smaydi, ya'ni baribir shu yerda ko'rishga to'g'ri
#     keladi.
# =====================================================================

import re as _pd_re  # noqa: E402

_PD_BUCKET = 10                    # bir bo'lak necha soniya
_PD_MAX_JUMP = 30                  # bitta xabarda ruxsat etilgan siljish
_PD_DONE = 90                      # necha foizdan keyin "ko'rildi"

# Kim video qo'sha oladi va statistikani ko'radi
_PD_MANAGE = [roles.FOUNDER, roles.HR_MANAGER]


if getattr(models, "PdVideo", None) is None:
    class PdVideo(_Base):
        """Shaxsiy rivojlanish videosi (YouTube yashirin havolasi)."""

        __tablename__ = "pd_videos"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, nullable=False)
        description = Column(String)
        topic = Column(String)               # bo'lim: "Dars metodikasi" ...
        yt_id = Column(String)               # YouTube video ID
        duration = Column(Integer, default=0)   # soniya
        target_roles = Column(String)        # bo'sh = hamma xodimga
        required = Column(Integer, default=1)
        order_no = Column(Integer, default=0)
        active = Column(Integer, default=1)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    class PdWatch(_Base):
        """Kim qaysi videoni qancha ko'rgani — bo'laklar xaritasi bilan."""

        __tablename__ = "pd_watch"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        video_id = Column(Integer, index=True, nullable=False)
        user_id = Column(Integer, index=True, nullable=False)
        marks = Column(String)                 # "0101..." har bo'lak uchun
        percent = Column(Integer, default=0)
        seconds = Column(Integer, default=0)   # ko'rilgan haqiqiy soniya
        max_pos = Column(Integer, default=0)   # eng uzoq borgan nuqta
        last_pos = Column(Integer, default=0)  # oxirgi xabardagi nuqta
        opens = Column(Integer, default=0)     # necha marta ochgan
        done = Column(Integer, default=0)
        done_at = Column(DateTime)
        first_at = Column(DateTime, default=_dt.utcnow)
        last_at = Column(DateTime, default=_dt.utcnow, onupdate=_dt.utcnow)

    models.PdVideo = PdVideo
    models.PdWatch = PdWatch
    try:
        _Base.metadata.create_all(
            bind=_engine, tables=[PdVideo.__table__, PdWatch.__table__])
    except Exception:
        pass

_PDV = models.PdVideo
_PDW = models.PdWatch


def _pd_yt(raw: str) -> str:
    """Havoladan YouTube ID ni ajratib olamiz.

    Direktor havolani qanday nusxalasa ham ishlasin: to'liq havola,
    youtu.be, embed, shorts yoki ID ning o'zi."""
    s = (raw or "").strip()
    if not s:
        return ""
    if _pd_re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _pd_re.search(
        r"(?:v=|/embed/|/shorts/|youtu\.be/|/live/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else ""


def _pd_buckets(duration: int) -> int:
    return max(1, -(-int(duration or 0) // _PD_BUCKET))


def _pd_marks(w, n: int) -> list:
    s = (w.marks or "") if w is not None else ""
    arr = [1 if c == "1" else 0 for c in s]
    if len(arr) < n:
        arr += [0] * (n - len(arr))
    return arr[:n]


def _pd_pct(arr: list) -> int:
    return round(sum(arr) * 100 / len(arr)) if arr else 0


def _pd_can_manage(user) -> bool:
    return user.role in tuple(_PD_MANAGE)


def _pd_for_role(v, role: str) -> bool:
    t = [x.strip() for x in (v.target_roles or "").split(",") if x.strip()]
    return (not t) or (role in t)


def _pd_hhmm(sec: int) -> str:
    sec = int(sec or 0)
    h, m = sec // 3600, (sec % 3600) // 60
    if h:
        return f"{h} soat {m} daq"
    if m:
        return f"{m} daq {sec % 60} son"
    return f"{sec} soniya"


def _pd_video_out(v, w=None) -> dict:
    return {
        "id": v.id, "title": v.title, "description": v.description or "",
        "topic": v.topic or "", "yt_id": v.yt_id or "",
        "duration": int(v.duration or 0),
        "minutes": round((v.duration or 0) / 60) or 1,
        "required": bool(v.required), "active": bool(v.active),
        "order_no": v.order_no or 0,
        "target_roles": [x for x in (v.target_roles or "").split(",") if x],
        "percent": int(getattr(w, "percent", 0) or 0),
        "done": bool(getattr(w, "done", 0)),
        "resume": int(getattr(w, "max_pos", 0) or 0),
    }


# --- Ustoz tomoni -----------------------------------------------------
@app.get("/api/pd/my")
def pd_my(db: Session = Depends(get_db), user=Depends(M.get_current_user)):
    """O'z ro'yxatim: qaysi videolar, qanchasini ko'rganman."""
    vids = [v for v in db.query(_PDV)
            .order_by(_PDV.order_no, _PDV.id).all()
            if v.active and _pd_for_role(v, user.role)]
    mine = {w.video_id: w for w in db.query(_PDW)
            .filter(_PDW.user_id == user.id).all()}
    rows = [_pd_video_out(v, mine.get(v.id)) for v in vids]

    req = [r for r in rows if r["required"]]
    done = [r for r in req if r["done"]]
    topics = []
    for r in rows:
        t = r["topic"] or "Umumiy"
        if t not in topics:
            topics.append(t)
    return {
        "items": rows, "topics": topics,
        "total": len(req), "done": len(done),
        "percent": round(len(done) * 100 / len(req)) if req else 0,
        # Suv belgisi uchun — ustozning o'zi
        "me": {"name": user.full_name or user.username,
               "phone": (getattr(user, "phone", "") or "")[-4:]},
        "watched_label": _pd_hhmm(
            sum(int(getattr(w, "seconds", 0) or 0) for w in mine.values())),
    }


@app.post("/api/pd/{video_id}/beat")
def pd_beat(video_id: int, payload: dict = Body(...),
            db: Session = Depends(get_db),
            user=Depends(M.get_current_user)):
    """Pleyer har necha soniyada shu yerga "qayerdaman" deb yozadi.

    Faqat shu nuqta atrofidagi bo'lak belgilanadi. Oldinga tashlab
    yuborilsa oradagi bo'laklar bo'sh qoladi — foiz oshmaydi."""
    v = db.query(_PDV).get(video_id)
    if not v or not v.active:
        raise HTTPException(404, "Video topilmadi")
    if not _pd_for_role(v, user.role) and not _pd_can_manage(user):
        raise HTTPException(403, "Bu video sizga tegishli emas")

    try:
        pos = int(float(payload.get("pos") or 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "Vaqt noto'g'ri")
    try:
        dur = int(float(payload.get("duration") or 0))
    except (TypeError, ValueError):
        dur = 0
    # Videoning uzunligini birinchi ko'rgan odam aniqlaydi
    if dur > 0 and abs((v.duration or 0) - dur) > 2:
        v.duration = dur
    dur = int(v.duration or dur or 0)
    n = _pd_buckets(dur)
    pos = max(0, min(pos, dur if dur else pos))

    w = (db.query(_PDW)
         .filter(_PDW.video_id == video_id, _PDW.user_id == user.id).first())
    if w is None:
        w = _PDW(video_id=video_id, user_id=user.id, marks="0" * n,
                 opens=1, last_pos=0, first_at=_dt.utcnow())
        db.add(w)
        db.flush()

    arr = _pd_marks(w, n)
    idx = min(n - 1, pos // _PD_BUCKET)
    # Qadam OXIRGI xabardagi nuqtadan o'lchanadi. Agar eng uzoq borgan
    # nuqtadan o'lchansa, videoni orqaga qaytarib qayta ko'rgan odamning
    # vaqti hisobga o'tmay qolardi.
    prev = int(getattr(w, "last_pos", 0) or 0)
    step = pos - prev

    # Tabiiy oqim bo'lsa — oradagi bo'laklarni ham belgilaymiz (xabar
    # kechikishi mumkin). Sakrash bo'lsa — faqat turgan bo'lagi.
    if 0 < step <= _PD_MAX_JUMP:
        for i in range(max(0, prev // _PD_BUCKET), idx + 1):
            arr[i] = 1
        w.seconds = int(w.seconds or 0) + step
    else:
        arr[idx] = 1
        w.seconds = int(w.seconds or 0) + min(_PD_BUCKET, max(0, step))

    w.marks = "".join(str(x) for x in arr)
    w.percent = _pd_pct(arr)
    w.max_pos = max(int(w.max_pos or 0), pos)
    w.last_pos = pos
    if w.percent >= _PD_DONE and not w.done:
        w.done = 1
        w.done_at = _dt.utcnow()
    db.commit()
    return {"percent": w.percent, "done": bool(w.done),
            "seconds": int(w.seconds or 0)}


@app.post("/api/pd/{video_id}/open")
def pd_open(video_id: int, db: Session = Depends(get_db),
            user=Depends(M.get_current_user)):
    """Videoni ochdi — necha marta ochgani ham foydali ko'rsatkich."""
    v = db.query(_PDV).get(video_id)
    if not v or not v.active:
        raise HTTPException(404, "Video topilmadi")
    w = (db.query(_PDW)
         .filter(_PDW.video_id == video_id, _PDW.user_id == user.id).first())
    if w is None:
        w = _PDW(video_id=video_id, user_id=user.id, opens=0,
                 marks="0" * _pd_buckets(v.duration))
        db.add(w)
    w.opens = int(w.opens or 0) + 1
    db.commit()
    return {"ok": True, "resume": int(w.max_pos or 0),
            "percent": int(w.percent or 0)}


# --- Boshqaruv: video qo'shish ----------------------------------------
@app.get("/api/pd/videos")
def pd_videos(db: Session = Depends(get_db),
              user=Depends(require_role(*_PD_MANAGE))):
    vids = db.query(_PDV).order_by(_PDV.order_no, _PDV.id).all()
    out = []
    for v in vids:
        ws = db.query(_PDW).filter(_PDW.video_id == v.id).all()
        row = _pd_video_out(v)
        row["watchers"] = len(ws)
        row["done_count"] = len([w for w in ws if w.done])
        row["avg_percent"] = (round(sum(int(w.percent or 0) for w in ws)
                                    / len(ws)) if ws else 0)
        out.append(row)
    return {"items": out, "can_manage": True,
            "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                      for r in roles.STAFF_ROLES]}


@app.post("/api/pd/videos")
def pd_video_add(payload: dict = Body(...), db: Session = Depends(get_db),
                 user=Depends(require_role(*_PD_MANAGE))):
    title = str(payload.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Video nomini kiriting")
    yt = _pd_yt(str(payload.get("yt") or payload.get("yt_id") or ""))
    if not yt:
        raise HTTPException(
            400, "YouTube havolasi noto'g'ri — havolani to'liq qo'ying")
    tr = payload.get("target_roles") or []
    v = _PDV(
        title=title,
        description=str(payload.get("description") or "").strip() or None,
        topic=str(payload.get("topic") or "").strip() or None,
        yt_id=yt,
        duration=int(payload.get("duration") or 0),
        target_roles=",".join(str(x) for x in tr) if tr else None,
        required=1 if payload.get("required", True) else 0,
        order_no=int(payload.get("order_no") or 0),
        active=1, created_by=user.username, created_at=_dt.utcnow())
    db.add(v)
    db.commit()
    return _pd_video_out(v)


@app.put("/api/pd/videos/{video_id}")
def pd_video_edit(video_id: int, payload: dict = Body(...),
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*_PD_MANAGE))):
    v = db.query(_PDV).get(video_id)
    if not v:
        raise HTTPException(404, "Topilmadi")
    if "title" in payload:
        t = str(payload["title"] or "").strip()
        if not t:
            raise HTTPException(400, "Nom bo'sh bo'lmasin")
        v.title = t
    if "yt" in payload or "yt_id" in payload:
        yt = _pd_yt(str(payload.get("yt") or payload.get("yt_id") or ""))
        if not yt:
            raise HTTPException(400, "YouTube havolasi noto'g'ri")
        if yt != v.yt_id:
            v.yt_id = yt
            v.duration = 0        # yangi video — uzunligi qaytadan
    for k in ("description", "topic"):
        if k in payload:
            setattr(v, k, str(payload[k] or "").strip() or None)
    if "target_roles" in payload:
        tr = payload.get("target_roles") or []
        v.target_roles = ",".join(str(x) for x in tr) if tr else None
    if "required" in payload:
        v.required = 1 if payload["required"] else 0
    if "active" in payload:
        v.active = 1 if payload["active"] else 0
    if "order_no" in payload:
        v.order_no = int(payload["order_no"] or 0)
    db.commit()
    return _pd_video_out(v)


@app.delete("/api/pd/videos/{video_id}")
def pd_video_del(video_id: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*_PD_MANAGE))):
    v = db.query(_PDV).get(video_id)
    if not v:
        raise HTTPException(404, "Topilmadi")
    db.query(_PDW).filter(_PDW.video_id == video_id).delete()
    db.delete(v)
    db.commit()
    return {"ok": True}


# --- Boshqaruv: statistika --------------------------------------------
@app.get("/api/pd/videos/{video_id}/people")
def pd_video_people(video_id: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*_PD_MANAGE))):
    """Shu videoni kim qancha ko'rgan."""
    v = db.query(_PDV).get(video_id)
    if not v:
        raise HTTPException(404, "Topilmadi")
    staff = [u for u in db.query(models.User)
             .filter(models.User.is_active == 1).all()
             if _pd_for_role(v, u.role)]
    ws = {w.user_id: w for w in db.query(_PDW)
          .filter(_PDW.video_id == video_id).all()}
    rows = []
    for u in staff:
        w = ws.get(u.id)
        rows.append({
            "user_id": u.id, "name": u.full_name or u.username,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "percent": int(getattr(w, "percent", 0) or 0),
            "done": bool(getattr(w, "done", 0)),
            "opens": int(getattr(w, "opens", 0) or 0),
            "seconds": int(getattr(w, "seconds", 0) or 0),
            "watched": _pd_hhmm(int(getattr(w, "seconds", 0) or 0)),
            "last_at": (w.last_at.strftime("%d.%m.%Y %H:%M")
                        if w is not None and w.last_at else None),
            "started": w is not None,
        })
    rows.sort(key=lambda r: (-r["percent"], r["name"]))
    return {"video": _pd_video_out(v), "rows": rows,
            "started": len([r for r in rows if r["started"]]),
            "done": len([r for r in rows if r["done"]]),
            "total": len(rows)}


@app.get("/api/pd/people")
def pd_people(db: Session = Depends(get_db),
              user=Depends(require_role(*_PD_MANAGE))):
    """Har bir xodim bo'yicha umumiy holat."""
    vids = [v for v in db.query(_PDV).all() if v.active]
    ws_all = db.query(_PDW).all()
    by_user = {}
    for w in ws_all:
        by_user.setdefault(w.user_id, []).append(w)
    vid_by_id = {v.id: v for v in vids}

    rows = []
    for u in db.query(models.User).filter(models.User.is_active == 1).all():
        mine = [v for v in vids if _pd_for_role(v, u.role) and v.required]
        if not mine:
            continue
        ws = [w for w in by_user.get(u.id, []) if w.video_id in vid_by_id]
        done = len([w for w in ws if w.done and w.video_id in
                    {v.id for v in mine}])
        sec = sum(int(w.seconds or 0) for w in ws)
        pcts = {w.video_id: int(w.percent or 0) for w in ws}
        avg = (round(sum(pcts.get(v.id, 0) for v in mine) / len(mine))
               if mine else 0)
        rows.append({
            "user_id": u.id, "name": u.full_name or u.username,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "total": len(mine), "done": done, "avg_percent": avg,
            "seconds": sec, "watched": _pd_hhmm(sec),
            "last_at": max([w.last_at for w in ws if w.last_at],
                           default=None),
        })
    for r in rows:
        r["last_at"] = (r["last_at"].strftime("%d.%m.%Y %H:%M")
                        if r["last_at"] else None)
    rows.sort(key=lambda r: (-r["avg_percent"], r["name"]))
    return {"rows": rows,
            "videos": len(vids),
            "avg_percent": (round(sum(r["avg_percent"] for r in rows)
                                  / len(rows)) if rows else 0),
            "watched_total": _pd_hhmm(sum(r["seconds"] for r in rows))}


@app.get("/api/pd/person/{user_id}")
def pd_person(user_id: int, db: Session = Depends(get_db),
              user=Depends(require_role(*_PD_MANAGE))):
    """Bitta xodim — qaysi videoni qancha ko'rgan."""
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    vids = [v for v in db.query(_PDV).order_by(_PDV.order_no, _PDV.id).all()
            if v.active and _pd_for_role(v, u.role)]
    ws = {w.video_id: w for w in db.query(_PDW)
          .filter(_PDW.user_id == user_id).all()}
    rows = []
    for v in vids:
        w = ws.get(v.id)
        rows.append({
            "video_id": v.id, "title": v.title, "topic": v.topic or "",
            "required": bool(v.required),
            "percent": int(getattr(w, "percent", 0) or 0),
            "done": bool(getattr(w, "done", 0)),
            "opens": int(getattr(w, "opens", 0) or 0),
            "watched": _pd_hhmm(int(getattr(w, "seconds", 0) or 0)),
            "last_at": (w.last_at.strftime("%d.%m.%Y %H:%M")
                        if w is not None and w.last_at else None),
        })
    req = [r for r in rows if r["required"]]
    return {"name": u.full_name or u.username,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "rows": rows,
            "total": len(req),
            "done": len([r for r in req if r["done"]]),
            "percent": (round(sum(r["percent"] for r in req) / len(req))
                        if req else 0)}

# =====================================================================
#  ADAPTIV INGLIZ TILI DIAGNOSTIKASI — LID UCHUN (_PT_*)
#
#  Odam markazga keladi yoki telefoniga havola olib, 50 savollik
#  testni ishlaydi. Har savolga 30 soniya. Test ADAPTIV: to'g'ri
#  javob — keyingi savol qiyinroq, xato — osonroq. Shu sababli 360
#  savollik bankdan har kishiga o'z yo'li tushadi, variant "qaysi
#  varaqni oldi"ga bog'liq emas.
#
#  Natija markaz bosqichlari tilida chiqadi: "Step 3 — B1 darajasi,
#  Unit 4 dan boshlang". Kitob nomi hech qayerda ko'rsatilmaydi
#  (2026-09-15). Daraja lidga o'zi yoziladi.
#
#  Havola BIR MARTALIK: ochilgach 48 soat amal qiladi, tugagach yoki
#  muddati o'tgach qayta ishlamaydi. Sessiya serverda yuritiladi —
#  javoblar brauzerda emas, shuning uchun sahifani yangilash yoki
#  "orqaga" bosish savolni qaytarmaydi.
# =====================================================================
import json as _pt_json          # noqa: E402
import random as _pt_random      # noqa: E402
import secrets as _pt_secrets    # noqa: E402
from datetime import datetime as _pt_dt, timedelta as _pt_td  # noqa: E402

from fastapi import Request as _pt_Request  # noqa: E402
from sqlalchemy import Column as _ptC, Integer as _ptI, String as _ptS, \
    Float as _ptF, DateTime as _ptDT, Text as _ptT  # noqa: E402

from pt_bank import PT_BANK, PT_LEVELS, PT_UNITS  # noqa: E402
from pt_vocab_bank import VOCAB_BY_ID, VOCAB_BY_LEVEL  # noqa: E402
from pt_read_bank import READ_BY_ID, READ_BY_LEVEL  # noqa: E402
from pt_listen_bank import LISTEN_BY_ID, LISTEN_BY_LEVEL  # noqa: E402

# 2026-09-11 — Jahongir: "grammar 30ta qolsin uzogi bilan grammar
# savoli" + "ichiga reading va listening lar ham qosha olmaysanmi".
#
# Grammatika 50 dan 30 ga tushdi: hisob-kitobga ko'ra 30 ta savol
# aniq darajaga tushish ehtimolini ~80% beradi (50 ta ~85%), farq
# kichik, lekin qolgan uch bo'limga joy ochiladi.
#
# BO'LIMLAR TARTIBI ATAYLAB SHUNDAY: grammatika BIRINCHI. Lid testni
# yarmida tashlab ketsa ham guruhga joylashtirish uchun kerak bo'lgan
# hamma narsa (daraja + unit) qo'lda bo'ladi.
_PT_N = 30                     # grammatika savollari soni
_PT_SECS = 30                  # bir savolga soniya
_PT_GRACE = 4                  # tarmoq kechikishi uchun qo'shimcha
_PT_TTL_H = 48                 # havola amal qilish muddati
_PT_START_D = 24               # boshlang'ich qiyinlik: B1 Unit 1
_PT_MAX_D = len(PT_LEVELS) * 12 - 1
_PT_BY_D = {}
for _q in PT_BANK:
    _PT_BY_D.setdefault(PT_LEVELS.index(_q["level"]) * 12 + _q["unit"] - 1,
                        []).append(_q)
_PT_BY_ID = {q["id"]: q for q in PT_BANK}
_PT_ROLES = list(dict.fromkeys(list(roles.LEAD_ACCESS)))

# ---- Yangi bo'limlar (2026-09-11) -----------------------------------
#  Har bo'lim bir xil "daraja zinasi" bo'yicha ishlaydi: yaxshi
#  javob — bir pog'ona tepaga, yomon javob — bir pog'ona pastga.
#  Boshlang'ich pog'ona grammatika natijasidan olinadi — ya'ni
#  lidni bejiz A1 dan boshlab charchatmaymiz.
_PT_SECTIONS = ("grammar", "vocab", "reading", "listening")
_PT_SEC_LABEL = {"grammar": "Grammatika", "vocab": "Lug'at",
                 "reading": "Reading", "listening": "Listening"}
_PT_SEC_N = {"vocab": 10, "reading": 5, "listening": 6}
_PT_VOCAB_SECS = 60
_PT_LISTEN_SECS = 90
_PT_LISTEN_PLAYS = 2
_PT_LMAX = len(PT_LEVELS) - 1
_PT_BANKS = {"vocab": (VOCAB_BY_LEVEL, VOCAB_BY_ID),
             "reading": (READ_BY_LEVEL, READ_BY_ID),
             "listening": (LISTEN_BY_LEVEL, LISTEN_BY_ID)}

if getattr(models, "PlacementSession", None) is None:
    class PlacementSession(_Base):
        __tablename__ = "placement_sessions"
        __table_args__ = {"extend_existing": True}

        id = _ptC(_ptI, primary_key=True, index=True)
        token = _ptC(_ptS, unique=True, index=True)
        lead_id = _ptC(_ptI, index=True)
        name = _ptC(_ptS)
        phone = _ptC(_ptS)
        mode = _ptC(_ptS, default="link")            # link | office
        status = _ptC(_ptS, default="new", index=True)  # new|running|done|expired
        branch_id = _ptC(_ptI)
        created_by = _ptC(_ptS)
        created_at = _ptC(_ptDT, default=_pt_dt.utcnow)
        expires_at = _ptC(_ptDT)
        started_at = _ptC(_ptDT)
        finished_at = _ptC(_ptDT)
        cur_d = _ptC(_ptI, default=_PT_START_D)
        step = _ptC(_ptI, default=6)
        cur_qid = _ptC(_ptI)
        cur_sent_at = _ptC(_ptDT)
        cur_shuffle = _ptC(_ptS)                       # "2,0,3,1"
        asked = _ptC(_ptT, default="[]")               # [qid,...]
        answers = _ptC(_ptT, default="[]")             # [{qid,d,ok,secs}]
        level = _ptC(_ptS)
        unit = _ptC(_ptI)
        score = _ptC(_ptI, default=0)
        ability = _ptC(_ptF)
        per_level = _ptC(_ptT)
        # 2026-09-11 — yangi bo'limlar. Ikkalasi ham nullable:
        # eski sessiyalarda bo'sh qoladi va ular avvalgidek
        # grammatika natijasi bilan ishlayveradi (hech narsa
        # yo'qolmaydi).
        sec = _ptC(_ptS)                               # joriy bo'lim
        sec_state = _ptC(_ptT)                         # JSON

    models.PlacementSession = PlacementSession
    _Base.metadata.create_all(bind=_engine, tables=[PlacementSession.__table__])

_PTS = models.PlacementSession


# ---- Yordamchilar ---------------------------------------------------
def _pt_now():
    return _pt_dt.utcnow()


def _pt_load(s):
    try:
        asked = _pt_json.loads(s.asked or "[]")
    except ValueError:
        asked = []
    try:
        answers = _pt_json.loads(s.answers or "[]")
    except ValueError:
        answers = []
    return asked, answers


def _pt_pick(d: int, asked: set, up: bool = True):
    """d ga eng yaqin, hali berilmagan savol. Avval shu unit, keyin
    qo'shni unitlar — yo'nalish bo'yicha (ko'tarilayotgan bo'lsa
    avval yuqoriroq unit)."""
    d = max(0, min(_PT_MAX_D, d))
    for off in range(0, _PT_MAX_D + 1):
        for cand in ((d + off, d - off) if up else (d - off, d + off)):
            if cand < 0 or cand > _PT_MAX_D:
                continue
            pool = [q for q in _PT_BY_D.get(cand, []) if q["id"] not in asked]
            if pool:
                return _pt_random.choice(pool), cand
    return None, d


def _pt_next_d(d: int, ok: bool, step: int, answers: list):
    """To'g'ri — yuqoriga, xato — pastga. Yo'nalish o'zgargan sari
    qadam kichrayadi (6 → 4 → 3 → 2), lekin 2 dan tushmaydi."""
    if len(answers) >= 2 and answers[-1]["ok"] != answers[-2]["ok"]:
        step = max(2, step - 1 if step <= 4 else step - 2)
    nd = d + step if ok else d - step
    return max(0, min(_PT_MAX_D, nd)), step


def _pt_serve(s, q):
    """Savolni yuboradi: variantlar aralashtiriladi, to'g'risi
    serverda qoladi."""
    order = list(range(4))
    _pt_random.shuffle(order)
    s.cur_qid = q["id"]
    s.cur_sent_at = _pt_now()
    s.cur_shuffle = ",".join(str(x) for x in order)
    asked, _ = _pt_load(s)
    asked.append(q["id"])
    s.asked = _pt_json.dumps(asked)
    return {"kind": "grammar", "section": "grammar",
            "section_label": _PT_SEC_LABEL["grammar"],
            "qid": q["id"], "no": len(asked), "total": _PT_N,
            "q": q["q"], "opts": [q["opts"][i] for i in order],
            "secs": _PT_SECS}


def _pt_finish(s):
    """Yakuniy baho: oxirgi 20 savolning qiyinlik o'rtachasi (to'g'ri
    javob berilgan qiyinlik yuqoriroq vazn oladi) → daraja va unit."""
    _, answers = _pt_load(s)
    tail = answers[-20:] if len(answers) > 20 else answers
    if not tail:
        ability = 0.0
    elif all(a["ok"] for a in tail):
        # shift: hammasi to'g'ri — eng yuqori yetgan nuqtadan ham yuqori
        ability = max(a["d"] for a in answers if a["ok"]) + 1
    elif not any(a["ok"] for a in tail):
        ability = min(a["d"] for a in answers if not a["ok"]) - 1
    else:
        # to'g'ri javob — shu nuqtadan biroz yuqori, xato — biroz past
        vals = [a["d"] + 2 if a["ok"] else a["d"] - 2 for a in tail]
        ability = sum(vals) / len(vals)
    ability = max(0.0, min(float(_PT_MAX_D), ability))
    li = int(ability // 12)
    unit = int(round(ability - li * 12)) + 1
    if unit > 12:
        unit = 12
    per = {}
    for a in answers:
        lv = PT_LEVELS[int(a["d"] // 12)]
        p = per.setdefault(lv, {"ok": 0, "n": 0})
        p["n"] += 1
        p["ok"] += 1 if a["ok"] else 0
    s.level = PT_LEVELS[li]
    s.unit = unit
    s.ability = round(ability, 2)
    s.score = sum(1 for a in answers if a["ok"])
    s.per_level = _pt_json.dumps(per)
    s.status = "done"
    s.finished_at = _pt_now()
    s.cur_qid = None


# =====================================================================
#  BO'LIM MASHINASI (2026-09-11) — vocab / reading / listening
#
#  Har bo'lim daraja zinasida yuradi (A1..C1). Boshlang'ich pog'ona
#  grammatika natijasidan olinadi. Yaxshi javob — tepaga, yomon —
#  pastga. Yakuniy daraja: har savoldagi pog'onaning o'rtachasi,
#  javob sifatiga qarab yarim pog'ona surilgan holda.
#
#  Holat BITTA JSON ustunda (sec_state) saqlanadi — shunda jadvalga
#  o'nlab ustun qo'shish shart emas va eski sessiyalar buzilmaydi.
#  To'g'ri javoblar bu yerda ham faqat serverda qoladi.
# =====================================================================
def _pt_sec_state(s) -> dict:
    try:
        st = _pt_json.loads(s.sec_state or "{}")
    except (ValueError, TypeError):
        st = {}
    return st if isinstance(st, dict) else {}


def _pt_sec_save(s, st) -> None:
    s.sec_state = _pt_json.dumps(st)


def _pt_start_li(s) -> int:
    """Boshlang'ich pog'ona — grammatika darajasi."""
    try:
        return max(0, min(_PT_LMAX, PT_LEVELS.index(s.level)))
    except (ValueError, TypeError):
        return 2


def _pt_sec_pick(sec: str, li: int, used: set):
    """li pog'onasiga eng yaqin, hali berilmagan savol."""
    by_level = _PT_BANKS[sec][0]
    li = max(0, min(_PT_LMAX, li))
    for off in range(0, _PT_LMAX + 1):
        for cand in (li + off, li - off):
            if cand < 0 or cand > _PT_LMAX:
                continue
            pool = [x for x in by_level.get(PT_LEVELS[cand], [])
                    if x["id"] not in used]
            if pool:
                return _pt_random.choice(pool), cand
    return None, li


def _pt_sec_secs(sec: str, item) -> int:
    if sec == "vocab":
        return _PT_VOCAB_SECS
    if sec == "reading":
        return int(item.get("secs") or 90)
    return _PT_LISTEN_SECS


def _pt_sec_payload(sec: str, item, cur: dict, no: int, left: int) -> dict:
    """Mijozga ketadigan savol. To'g'ri javob HECH QACHON qo'shilmaydi."""
    base = {"kind": sec, "qid": item["id"], "no": no,
            "total": _PT_SEC_N[sec], "section": sec,
            "section_label": _PT_SEC_LABEL[sec], "secs": left,
            "full_secs": _pt_sec_secs(sec, item)}
    if sec == "vocab":
        w = cur["w"]
        d = cur["d"]
        base["words"] = [item["words"][i] for i in w]
        base["defs"] = [item["defs"][j][0] for j in d]
        return base
    if sec == "reading":
        base["text"] = item["text"]
        base["qs"] = [{"q": item["qs"][i]["q"],
                       "opts": [item["qs"][i]["opts"][k]
                                for k in cur["o"][i]]}
                      for i in range(len(item["qs"]))]
        return base
    base["script"] = item["script"]
    base["rate"] = item.get("rate") or 1.0
    base["plays"] = _PT_LISTEN_PLAYS
    base["q"] = item["q"]
    base["opts"] = [item["opts"][k] for k in cur["o"]]
    return base


def _pt_sec_serve(s, sec: str, item, li: int) -> dict:
    """Yangi savolni tayyorlaydi: variantlar aralashtiriladi."""
    cur = {"id": item["id"], "li": li, "sent": _pt_now().isoformat()}
    if sec == "vocab":
        w = list(range(len(item["words"])))
        d = list(range(len(item["defs"])))
        _pt_random.shuffle(w)
        _pt_random.shuffle(d)
        cur["w"], cur["d"] = w, d
    elif sec == "reading":
        o = []
        for q in item["qs"]:
            p = list(range(len(q["opts"])))
            _pt_random.shuffle(p)
            o.append(p)
        cur["o"] = o
    else:
        p = list(range(len(item["opts"])))
        _pt_random.shuffle(p)
        cur["o"] = p
    st = _pt_sec_state(s)
    sst = st.setdefault(sec, {"li": li, "done": []})
    sst["li"] = li
    sst["cur"] = cur
    _pt_sec_save(s, st)
    no = len(sst.get("done") or []) + 1
    return _pt_sec_payload(sec, item, cur, no, _pt_sec_secs(sec, item))


def _pt_sec_left(sec: str, item, cur: dict) -> int:
    full = _pt_sec_secs(sec, item)
    try:
        sent = _pt_dt.fromisoformat(cur.get("sent") or "")
    except (ValueError, TypeError):
        return full
    return max(0, full - int((_pt_now() - sent).total_seconds()))


def _pt_sec_grade(sec: str, item, cur: dict, payload: dict):
    """(olingan ball, eng ko'p ball). Vaqt tugagan bo'lsa — 0."""
    mx = 3 if sec == "vocab" else (len(item.get("qs", [])) if sec == "reading"
                                   else 1)
    full = _pt_sec_secs(sec, item)
    try:
        sent = _pt_dt.fromisoformat(cur.get("sent") or "")
        late = (_pt_now() - sent).total_seconds() > full + _PT_GRACE
    except (ValueError, TypeError):
        late = False
    if late:
        return 0, mx, True
    got = 0
    if sec == "vocab":
        picks = payload.get("picks") or []
        for j, dj in enumerate(cur["d"]):
            try:
                k = int(picks[j])
                if cur["w"][k] == item["defs"][dj][1]:
                    got += 1
            except (TypeError, ValueError, IndexError):
                pass
    elif sec == "reading":
        picks = payload.get("picks") or []
        for i, q in enumerate(item["qs"]):
            try:
                if cur["o"][i][int(picks[i])] == q["a"]:
                    got += 1
            except (TypeError, ValueError, IndexError):
                pass
    else:
        try:
            if cur["o"][int(payload.get("choice"))] == item["a"]:
                got = 1
        except (TypeError, ValueError, IndexError):
            got = 0
    return got, mx, False


def _pt_sec_next_li(li: int, got: int, mx: int) -> int:
    """Yarmidan ko'p — tepaga, yarmidan kam — pastga, roppa-rosa
    yarmi — o'sha joyda."""
    if got * 2 > mx:
        li += 1
    elif got * 2 < mx:
        li -= 1
    return max(0, min(_PT_LMAX, li))


def _pt_sec_level(sst: dict) -> str:
    """Bo'lim yakuniy darajasi.

    MUHIM: hamma savolning o'rtachasi OLINMAYDI. Bo'lim boshida
    test hali darajani QIDIRAYOTGAN bo'ladi — agar lid A1 dan
    boshlanib C1 gacha ko'tarilsa, yo'ldagi past pog'onalar
    o'rtachani pastga tortib, C1 bilgan odamga B2 chiqarib qo'yardi.
    Shuning uchun faqat OXIRGI yarmi — ya'ni test qayerga
    o'rnashgani — hisobga olinadi. Bu grammatika bo'limidagi
    mantiqning aynan o'zi (u ham oxirgi savollarga qaraydi).

    Hammasi to'g'ri bo'lsa — yetgan eng yuqori pog'onadan ham
    yuqori; hammasi xato bo'lsa — eng pastidan ham past."""
    done = sst.get("done") or []
    if not done:
        return None

    def _mx(a):
        return max(1, int(a.get("max") or 1))

    def _contrib(a):
        return (float(a.get("li") or 0)
                + (float(a.get("score") or 0) / _mx(a) - 0.5))

    if all(int(a.get("score") or 0) >= _mx(a) for a in done):
        ab = max(float(a.get("li") or 0) for a in done) + 0.5
    elif all(int(a.get("score") or 0) == 0 for a in done):
        ab = min(float(a.get("li") or 0) for a in done) - 0.5
    else:
        vals = [_contrib(a) for a in done]
        k = max(3, len(vals) // 2)
        tail = vals[-k:]
        ab = sum(tail) / len(tail)
    return PT_LEVELS[max(0, min(_PT_LMAX, int(round(ab))))]


def _pt_next_section(sec: str):
    i = _PT_SECTIONS.index(sec) if sec in _PT_SECTIONS else 0
    return _PT_SECTIONS[i + 1] if i + 1 < len(_PT_SECTIONS) else None


def _pt_open_section(s, sec: str):
    """Bo'limni ochadi va birinchi savolini beradi. Bank bo'sh
    bo'lsa — keyingisiga o'tadi."""
    while sec:
        li = _pt_start_li(s)
        item, li = _pt_sec_pick(sec, li, set())
        if item is not None:
            s.sec = sec
            return _pt_sec_serve(s, sec, item, li)
        sec = _pt_next_section(sec)
    s.sec = "done"
    return None


def _pt_all_done(s) -> None:
    s.sec = "done"
    s.status = "done"
    s.finished_at = _pt_now()
    s.cur_qid = None


def _pt_break(db, s, sec_done: dict, nxt: str) -> dict:
    """Bo'limlar orasidagi tanaffus.

    MUHIM: keyingi savol SHU YERDA berilmaydi. Aks holda lid tanaffus
    ekranida o'tirganda savol soati allaqachon ketayotgan bo'lardi va
    u vaqtini bekorga yo'qotardi. Savol faqat "Davom etish" bosilgach
    (/start orqali) beriladi."""
    if not nxt:
        _pt_all_done(s)
        _pt_apply_to_lead(db, s)
        db.commit()
        return {"status": "done", "result": _pt_result(s)}
    s.sec = nxt
    s.status = "running"
    s.finished_at = None
    s.cur_qid = None
    db.commit()
    return {"status": "break", "section_done": sec_done,
            "next": nxt, "next_label": _PT_SEC_LABEL[nxt],
            "next_total": _PT_SEC_N.get(nxt)}


def _pt_after_grammar(db, s) -> dict:
    """Grammatika tugadi: natija hisoblanadi va DARROV lidga yoziladi
    — lid qolgan bo'limlarni tashlab ketsa ham joylashtirish uchun
    hamma narsa bo'ladi."""
    _pt_finish(s)                      # daraja + unit hisoblanadi
    _pt_apply_to_lead(db, s)
    return _pt_break(db, s, {"key": "grammar",
                             "label": _PT_SEC_LABEL["grammar"],
                             "level": s.level, "unit": s.unit},
                     _pt_next_section("grammar"))


def _pt_sec_answer(db, s, payload: dict) -> dict:
    """Yangi bo'limlardagi javob."""
    sec = s.sec
    st = _pt_sec_state(s)
    sst = st.get(sec) or {}
    cur = sst.get("cur")
    if not cur:
        raise HTTPException(409, "Faol savol yo'q")
    item = _PT_BANKS[sec][1].get(cur["id"])
    if item is None:
        raise HTTPException(409, "Faol savol yo'q")
    try:
        qid = int(payload.get("qid") or 0)
    except (TypeError, ValueError):
        qid = 0
    if qid and qid != cur["id"]:
        return _pt_state_dict(s)       # eski savol — hozirgisini beramiz
    got, mx, late = _pt_sec_grade(sec, item, cur, payload)
    done = sst.setdefault("done", [])
    done.append({"id": cur["id"], "li": int(cur["li"]), "score": got,
                 "max": mx, "t": bool(late)})
    li = _pt_sec_next_li(int(cur["li"]), got, mx)
    sst["li"] = li
    sst.pop("cur", None)
    used = {a["id"] for a in done}
    nxt_item = None
    if len(done) < _PT_SEC_N[sec]:
        nxt_item, li = _pt_sec_pick(sec, li, used)
    if nxt_item is not None:
        st[sec] = sst
        _pt_sec_save(s, st)
        q = _pt_sec_serve(s, sec, nxt_item, li)
        db.commit()
        return {"status": "running", "question": q}
    # bo'lim tugadi
    sst["level"] = _pt_sec_level(sst)
    st[sec] = sst
    _pt_sec_save(s, st)
    return _pt_break(db, s, {"key": sec, "label": _PT_SEC_LABEL[sec],
                             "level": sst.get("level")},
                     _pt_next_section(sec))


def _pt_sec_skip(db, s) -> dict:
    """Listening bo'limini o'tkazib yuborish — faqat brauzerda ovoz
    ishlamagan holat uchun. Jazo yo'q: natijada "tekshirilmadi" deb
    yoziladi, taxminiy daraja qo'yilmaydi."""
    sec = s.sec
    if sec != "listening":
        raise HTTPException(400, "Bu bo'limni o'tkazib bo'lmaydi")
    st = _pt_sec_state(s)
    sst = st.get(sec) or {"li": _pt_start_li(s), "done": []}
    sst["skipped"] = True
    sst["level"] = None
    sst.pop("cur", None)
    st[sec] = sst
    _pt_sec_save(s, st)
    return _pt_break(db, s, {"key": sec, "label": _PT_SEC_LABEL[sec],
                             "level": None, "skipped": True},
                     _pt_next_section(sec))


def _pt_state_dict(s) -> dict:
    """Joriy holat — qaysi bo'limda bo'lsa ham."""
    out = {"name": s.name, "status": s.status, "n": _PT_N,
           "secs": _PT_SECS, "answered": len(_pt_load(s)[1]),
           "section": s.sec or "grammar"}
    if s.status == "done":
        out["result"] = _pt_result(s)
        out["finished_at"] = (s.finished_at.isoformat()
                              if s.finished_at else None)
        return out
    if s.status != "running":
        return out
    sec = s.sec or "grammar"
    if sec == "grammar" and s.cur_qid:
        q = _PT_BY_ID[s.cur_qid]
        order = [int(x) for x in (s.cur_shuffle or "0,1,2,3").split(",")]
        left = _PT_SECS
        if s.cur_sent_at:
            left = max(0, _PT_SECS
                       - int((_pt_now() - s.cur_sent_at).total_seconds()))
        out["question"] = {"kind": "grammar", "qid": q["id"],
                           "no": len(_pt_load(s)[0]), "total": _PT_N,
                           "section": "grammar",
                           "section_label": _PT_SEC_LABEL["grammar"],
                           "q": q["q"],
                           "opts": [q["opts"][i] for i in order],
                           "secs": left, "full_secs": _PT_SECS}
    elif sec in _PT_BANKS:
        sst = _pt_sec_state(s).get(sec) or {}
        cur = sst.get("cur")
        item = _PT_BANKS[sec][1].get(cur["id"]) if cur else None
        if item is not None:
            out["question"] = _pt_sec_payload(
                sec, item, cur, len(sst.get("done") or []) + 1,
                _pt_sec_left(sec, item, cur))
    if "question" not in out:
        # Tanaffusda (yoki sahifa yangilangan) — savol hali
        # berilmagan. Mijoz "Davom etish" bosib /start ga murojaat
        # qiladi, soat o'shanda boshlanadi.
        out["status"] = "break"
        out["next"] = sec
        out["next_label"] = _PT_SEC_LABEL.get(sec, "")
        out["next_total"] = _PT_SEC_N.get(sec)
    return out


# NATIJA KITOB NOMISIZ (2026-09-15, Jahongir: "umuman empower
# demasin ... Step 1 - A1 darajasi, Step 2 A2 darajasi shunaqa qib
# korsatsin qaysi kitobdan otayotganimiz bilinmasin"). Markaz
# bosqichlari: Step 1..4, undan keyin IELTS.
_PT_STEP = {"A1": "Step 1", "A2": "Step 2", "B1": "Step 3",
            "B1+": "Step 4", "B2": "IELTS", "C1": "IELTS"}


def _pt_step_label(lv) -> str:
    return f"{_PT_STEP.get(lv, lv)} — {lv} darajasi" if lv else "—"


def _pt_topics(s) -> list:
    """Grammatika MAVZULAR kesimida: har mavzuda nechta savol, nechtasi
    to'g'ri, foizi (2026-09-15, Jahongir: "test chuqur tahlil mavzular
    kesimida natijalarni foiz korinishida bersin")."""
    _, answers = _pt_load(s)
    agg = {}
    for a in answers:
        li = max(0, min(len(PT_LEVELS) - 1, int(a["d"] // 12)))
        u = int(a["d"] % 12)
        lv = PT_LEVELS[li]
        names = PT_UNITS.get(lv) or []
        p = agg.setdefault((li, u), {
            "level": lv, "step": _PT_STEP.get(lv, lv), "unit": u + 1,
            "topic": names[u] if u < len(names) else f"Unit {u + 1}",
            "ok": 0, "n": 0})
        p["n"] += 1
        p["ok"] += 1 if a["ok"] else 0
    return [dict(p, pct=round(p["ok"] * 100 / p["n"]))
            for _k, p in sorted(agg.items())]


def _pt_result(s) -> dict:
    try:
        per = _pt_json.loads(s.per_level or "{}")
    except ValueError:
        per = {}
    lv = s.level or "A1"
    unit = int(s.unit or 1)
    topic = PT_UNITS.get(lv, [""] * 12)[unit - 1] if 1 <= unit <= 12 else ""
    # Tavsiya: unit 1-2 bo'lsa kitob boshidan; 11-12 bo'lsa keyingi
    # daraja boshidan ham o'ylab ko'rish mumkin
    nxt = None
    if unit >= 11 and PT_LEVELS.index(lv) < len(PT_LEVELS) - 1:
        nxt = PT_LEVELS[PT_LEVELS.index(lv) + 1]
    # Ko'nikmalar kesimi (2026-09-11). Bo'lim tugallanmagan bo'lsa
    # "—" ko'rsatiladi: taxmin qilib raqam yozmaymiz.
    st = _pt_sec_state(s)
    _g_ans = _pt_load(s)[1]
    _g_n = len(_g_ans)
    # Foiz javoblarning o'zidan: eski sessiyalarda score ustuni javoblar
    # soniga mos kelmasligi mumkin (100% dan oshib ketmasin)
    grammar_pct = (round(sum(1 for a in _g_ans if a.get("ok")) * 100 / _g_n)
                   if _g_n else 0)
    skills = [{"key": "grammar", "label": _PT_SEC_LABEL["grammar"],
               "level": lv, "n": _g_n, "pct": grammar_pct,
               "done": True, "skipped": False}]
    for _k in ("vocab", "reading", "listening"):
        _sst = st.get(_k) or {}
        _done = _sst.get("done") or []
        _sk = bool(_sst.get("skipped"))
        _mx = sum(float(x.get("max") or 0) for x in _done)
        skills.append({
            "key": _k, "label": _PT_SEC_LABEL[_k],
            "level": _sst.get("level") or (None if _sk else
                                           _pt_sec_level(_sst)),
            "pct": (round(sum(float(x.get("score") or 0) for x in _done)
                          * 100 / _mx) if _mx else None),
            "n": len(_done), "total": _PT_SEC_N[_k],
            "done": len(_done) >= _PT_SEC_N[_k], "skipped": _sk})
    _li = [PT_LEVELS.index(x["level"]) for x in skills
           if x.get("level") in PT_LEVELS]
    overall = PT_LEVELS[int(round(sum(_li) / len(_li)))] if _li else lv
    topics = _pt_topics(s)
    return {
        "level": lv, "unit": unit, "topic": topic,
        "score": int(s.score or 0), "total": len(_pt_load(s)[1]) or _PT_N,
        "ability": s.ability,
        "per_level": [{"level": k, "ok": v["ok"], "n": v["n"],
                       "pct": round(v["ok"] * 100 / v["n"]) if v["n"] else 0}
                      for k, v in per.items()],
        # "book" kaliti eski ekranlar uchun qoldi — endi kitob nomi emas
        "book": _pt_step_label(lv),
        "step": _PT_STEP.get(lv, lv),
        "skills": skills,
        "overall": overall,
        "overall_label": _pt_step_label(overall),
        "grammar_pct": grammar_pct,
        "topics": topics,
        "strong": [t for t in topics if t["n"] >= 2 and t["pct"] >= 75],
        "weak": [t for t in topics if t["pct"] < 50],
        "advice": (f"{_pt_step_label(lv)}, Unit {unit} dan boshlash tavsiya etiladi"
                   + (f" (yoki {_pt_step_label(nxt)} boshidan)." if nxt else ".")),
        "note": ("Guruhga joylashtirish grammatika darajasi bo'yicha "
                 "bo'ladi. Reading va Listening ustozga qo'shimcha "
                 "ma'lumot uchun. Speaking va Writing sinov darsda "
                 "tekshiriladi."),
    }


def _pt_out(s, db=None) -> dict:
    d = {"id": s.id, "token": s.token, "lead_id": s.lead_id, "name": s.name,
         "phone": s.phone, "mode": s.mode, "status": s.status,
         "created_by": s.created_by,
         "created_at": s.created_at.isoformat() if s.created_at else None,
         "expires_at": s.expires_at.isoformat() if s.expires_at else None,
         "finished_at": s.finished_at.isoformat() if s.finished_at else None,
         "answered": len(_pt_load(s)[1]),
         "section": s.sec or "grammar",
         "section_label": _PT_SEC_LABEL.get(s.sec or "grammar", "—")}
    if s.status == "done":
        d["result"] = _pt_result(s)
    return d


def _pt_base_url(request) -> str:
    host = (request.headers.get("x-forwarded-host")
            or request.headers.get("host") or "jony-crm.vercel.app")
    proto = request.headers.get("x-forwarded-proto") or "https"
    return f"{proto}://{host}"


def _pt_expire_if_needed(s) -> bool:
    if s.status in ("new", "running") and s.expires_at and s.expires_at < _pt_now():
        s.status = "expired"
        return True
    return False


# ---- Xodim: sessiya ochish, ro'yxat ---------------------------------
@app.post("/api/placement/sessions")
def pt_create(request: _pt_Request, payload: dict = Body(...),
              db: Session = Depends(get_db),
              user=Depends(require_role(*_PT_ROLES))):
    """Lid uchun test: office (shu yerda ishlaydi) yoki link (telefonga)."""
    lead = None
    lid = payload.get("lead_id")
    if lid:
        lead = db.query(models.Lead).get(int(lid))
        if lead is None:
            raise HTTPException(404, "Lid topilmadi")
    name = str(payload.get("name") or (lead.full_name if lead else "")).strip()
    phone = str(payload.get("phone") or (lead.phone if lead else "") or "").strip()
    if not name:
        raise HTTPException(400, "Ism kiriting")
    mode = "office" if str(payload.get("mode") or "link") == "office" else "link"
    # Bitta lidga ochiq sessiya bo'lsa — o'shani qaytaramiz
    if lead is not None:
        old = (db.query(_PTS).filter(_PTS.lead_id == lead.id,
                                     _PTS.status.in_(("new", "running"))).first())
        if old is not None and not _pt_expire_if_needed(old):
            base = _pt_base_url(request)
            return {"ok": True, "session": _pt_out(old),
                    "url": f"{base}/placement.html?t={old.token}", "reused": True}
    s = _PTS(token=_pt_secrets.token_urlsafe(18), lead_id=lead.id if lead else None,
             name=name[:120], phone=phone[:40] or None, mode=mode,
             branch_id=getattr(user, "branch_id", None),
             created_by=getattr(user, "full_name", None) or user.username,
             expires_at=_pt_now() + _pt_td(hours=_PT_TTL_H))
    db.add(s)
    db.commit()
    db.refresh(s)
    audit.log(db, user, entity="placement", action="create", entity_id=s.id,
              entity_label=name, new_value=mode, commit=True)
    base = _pt_base_url(request)
    return {"ok": True, "session": _pt_out(s),
            "url": f"{base}/placement.html?t={s.token}", "reused": False}


@app.get("/api/placement/sessions")
def pt_list(limit: int = 50, lead_id: int | None = None,
            db: Session = Depends(get_db),
            user=Depends(require_role(*_PT_ROLES))):
    q = db.query(_PTS)
    if lead_id:
        q = q.filter(_PTS.lead_id == int(lead_id))
    rows = q.order_by(_PTS.id.desc()).limit(max(1, min(300, int(limit)))).all()
    changed = False
    for s in rows:
        changed = _pt_expire_if_needed(s) or changed
    if changed:
        db.commit()
    return {"rows": [_pt_out(s) for s in rows],
            "levels": PT_LEVELS, "n": _PT_N, "secs": _PT_SECS}


@app.get("/api/placement/sessions/{sid}")
def pt_get(sid: int, db: Session = Depends(get_db),
           user=Depends(require_role(*_PT_ROLES))):
    s = db.query(_PTS).get(sid)
    if s is None:
        raise HTTPException(404, "Sessiya topilmadi")
    d = _pt_out(s)
    _, answers = _pt_load(s)
    d["answers"] = [{**a, "level": PT_LEVELS[int(a["d"] // 12)],
                     "unit": int(a["d"] % 12) + 1,
                     "q": _PT_BY_ID.get(a["qid"], {}).get("q")} for a in answers]
    return d


@app.delete("/api/placement/sessions/{sid}")
def pt_delete(sid: int, db: Session = Depends(get_db),
              user=Depends(require_role(*_PT_ROLES))):
    s = db.query(_PTS).get(sid)
    if s is None:
        raise HTTPException(404, "Sessiya topilmadi")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---- Ochiq (loginsiz): test o'zi ------------------------------------
def _pt_public(db, token: str):
    s = db.query(_PTS).filter(_PTS.token == token).first()
    if s is None:
        raise HTTPException(404, "Havola noto'g'ri yoki o'chirilgan")
    if _pt_expire_if_needed(s):
        db.commit()
    return s


@app.get("/api/public/placement/{token}")
def pt_state(token: str, db: Session = Depends(get_db)):
    return _pt_state_dict(_pt_public(db, token))


@app.post("/api/public/placement/{token}/start")
def pt_start(token: str, payload: dict = Body(default={}),
             db: Session = Depends(get_db)):
    s = _pt_public(db, token)
    if s.status == "expired":
        raise HTTPException(410, "Havola muddati tugagan")
    if s.status == "done":
        raise HTTPException(409, "Test allaqachon yakunlangan")
    if s.status == "running":
        sec = s.sec or "grammar"
        st = _pt_state_dict(s)
        if st.get("question"):
            return st           # savol allaqachon berilgan — o'shani
        if sec in _PT_BANKS:
            # Tanaffusdan keyin "Davom etish": savol SHU YERDA
            # beriladi, soat ham shu yerdan boshlanadi.
            q = _pt_open_section(s, sec)
            if q is None:
                _pt_all_done(s)
                _pt_apply_to_lead(db, s)
                db.commit()
                return {"status": "done", "result": _pt_result(s)}
            db.commit()
            return {"status": "running", "name": s.name, "question": q}
    if payload.get("name") and not s.name:
        s.name = str(payload["name"]).strip()[:120]
    s.status = "running"
    s.sec = "grammar"
    s.started_at = s.started_at or _pt_now()
    s.expires_at = _pt_now() + _pt_td(hours=_PT_TTL_H)
    q, d = _pt_pick(s.cur_d or _PT_START_D, set())
    s.cur_d = d
    qd = _pt_serve(s, q)
    db.commit()
    return {"status": "running", "name": s.name, "question": qd}


@app.post("/api/public/placement/{token}/answer")
def pt_answer(token: str, payload: dict = Body(...),
              db: Session = Depends(get_db)):
    s = _pt_public(db, token)
    if s.status != "running":
        raise HTTPException(409, "Faol savol yo'q")
    # Yangi bo'limlar (lug'at / reading / listening) alohida yuriladi.
    if (s.sec or "grammar") in _PT_BANKS:
        if payload.get("skip_section"):
            return _pt_sec_skip(db, s)
        return _pt_sec_answer(db, s, payload)
    if not s.cur_qid:
        raise HTTPException(409, "Faol savol yo'q")
    try:
        qid = int(payload.get("qid") or 0)
    except (TypeError, ValueError):
        qid = 0
    if qid != s.cur_qid:
        # eski savolga javob — hozirgi savolni qaytaramiz
        return pt_state(token, db)
    q = _PT_BY_ID[qid]
    order = [int(x) for x in (s.cur_shuffle or "0,1,2,3").split(",")]
    choice = payload.get("choice")
    secs = int((_pt_now() - s.cur_sent_at).total_seconds()) if s.cur_sent_at else 0
    timed_out = secs > _PT_SECS + _PT_GRACE or choice is None
    ok = False
    if not timed_out:
        try:
            ok = order[int(choice)] == q["a"]
        except (TypeError, ValueError, IndexError):
            ok = False
    asked, answers = _pt_load(s)
    answers.append({"qid": qid, "d": int(s.cur_d or 0), "ok": bool(ok),
                    "secs": min(secs, _PT_SECS + _PT_GRACE),
                    "t": bool(timed_out)})
    s.answers = _pt_json.dumps(answers)
    nd, step = _pt_next_d(int(s.cur_d or 0), ok, int(s.step or 6), answers)
    s.step = step
    if len(answers) >= _PT_N:
        return _pt_after_grammar(db, s)
    nq, d = _pt_pick(nd, set(asked), up=ok)
    if nq is None:
        return _pt_after_grammar(db, s)
    s.cur_d = d
    qd = _pt_serve(s, nq)
    db.commit()
    return {"status": "running", "question": qd, "last_ok": ok}


def _pt_apply_to_lead(db, s) -> None:
    """Natija lidga: darajasi izohga yoziladi (ustun bo'lmasa ham
    yo'qolmaydi) va lid ro'yxatida 'placement' bo'lib chiqadi."""
    if not s.lead_id:
        return
    lead = db.query(models.Lead).get(s.lead_id)
    if lead is None:
        return
    r = _pt_result(s)
    tag = f"[Diagnostika] {r['level']}, Unit {r['unit']} — {r['score']}/{r['total']}"
    # Ko'nikmalar tugagan bo'lsa ular ham yoziladi (2026-09-11).
    _sk = [f"{x['label']} {x['level']}" for x in (r.get("skills") or [])
           if x.get("key") != "grammar" and x.get("level")]
    if _sk:
        tag += " · " + ", ".join(_sk)
    note = lead.note or ""
    if "[Diagnostika]" in note:
        lines = [ln for ln in note.split("\n") if "[Diagnostika]" not in ln]
        note = "\n".join(lines).strip()
    lead.note = (tag + ("\n" + note if note else ""))[:2000]
    try:
        if hasattr(lead, "level"):
            lead.level = r["level"]
    except Exception:
        pass


# ---- Lid ro'yxatida daraja ------------------------------------------
_pt_leads_v1 = _find_endpoint("/api/leads", "GET")
if _pt_leads_v1 is not None:
    _drop_route("/api/leads", "GET")

    @app.get("/api/leads")
    def list_leads_pt(stage: str | None = None, branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.LEAD_ACCESS))):
        rows = _pt_leads_v1(stage=stage, branch_id=branch_id, db=db, user=user)
        out = []
        for x in rows or []:
            if isinstance(x, dict):
                out.append(dict(x))
            elif hasattr(x, "model_dump"):
                out.append(x.model_dump())
            else:
                try:
                    out.append(schemas.LeadOut.model_validate(x).model_dump())
                except Exception:
                    out.append({"id": getattr(x, "id", None),
                                "full_name": getattr(x, "full_name", None)})
        ids = [r.get("id") for r in out if r.get("id")]
        if ids:
            done = {}
            for s in (db.query(_PTS).filter(_PTS.lead_id.in_(ids),
                                            _PTS.status == "done")
                      .order_by(_PTS.id.asc()).all()):
                done[s.lead_id] = _pt_result(s) | {"session_id": s.id,
                                                   "date": (s.finished_at or s.created_at).date().isoformat()}
            open_ = {}
            for s in (db.query(_PTS).filter(_PTS.lead_id.in_(ids),
                                            _PTS.status.in_(("new", "running"))).all()):
                open_[s.lead_id] = {"session_id": s.id, "status": s.status,
                                    "token": s.token}
            for r in out:
                r["placement"] = done.get(r.get("id"))
                r["placement_open"] = open_.get(r.get("id"))
            # BARABAN (2026-09-25): lidga tushgan sovg'a ro'yxatda
            # ko'rinsin — admin o'quvchi ochayotganda bilib tursin.
            try:
                import wheel as _wheel
                _sp = {}
                for w in (db.query(models.WheelSpin)
                          .filter(models.WheelSpin.lead_id.in_(ids))
                          .order_by(models.WheelSpin.id.asc()).all()):
                    _sp.setdefault(w.lead_id, w)
                _pz = _wheel.active_prizes(db)
                for r in out:
                    w = _sp.get(r.get("id"))
                    r["wheel"] = _wheel.spin_out(db, w, _pz) if w else None
            except Exception:
                pass
        return out


# ---- Baraban: ochiq endpointlar (test sahifasi uchun) ----------------
#  Sovg'ani SERVER tanlaydi va yozadi; telefon faqat animatsiya qiladi.
@app.get("/api/public/placement/{token}/wheel")
def pt_wheel_state(token: str, db: Session = Depends(get_db)):
    import wheel as _wheel
    return _wheel.state_for_session(db, _pt_public(db, token))


@app.post("/api/public/placement/{token}/wheel/spin")
def pt_wheel_spin(token: str, db: Session = Depends(get_db)):
    import wheel as _wheel
    s = _pt_public(db, token)
    spin, created = _wheel.spin_for_session(db, s)
    out = _wheel.spin_out(db, spin)
    out["created"] = created
    return out


# =====================================================================
#  CHEGIRMASIZ YECHILGAN OYLIK HISOBLARNI TO'G'RILASH (2026-09-06)
#
#  Jahongir: "togrla hamma aytganingni" — auditda topilgan xato:
#  avtomat oylik yechim (_mc_charge_full) chegirmani UMUMAN ko'rmasdi,
#  chegirmali o'quvchidan to'liq narx yechilardi. Kod tuzatildi; bu
#  yerda ALLAQACHON yechilgan qatorlar to'g'rilanadi: summa JOYIDA
#  kamayadi (qator o'chirilmaydi), eski qiymat auditda qoladi.
#  Har oy uchun alohida belgi — keyingi oyda yangisi bilan ishlaydi.
# =====================================================================
try:
    from sqlalchemy.orm import Session as _VS34
    from common import _seed_done as _sd34, _seed_mark as _sm34
    from database import engine as _EN34
    with _VS34(_EN34) as _db34:
        _t34 = roles.local_today()
        _key34 = f"disc_charge_fix_{_t34.year:04d}-{_t34.month:02d}"
        if not _sd34(_db34, _key34):
            _r34 = fix_discount_charges(_db34)
            _sm34(_db34, _key34)
            if _r34.get("fixed"):
                print(f"[seed] chegirmasiz yechilgan hisoblar: "
                      f"{_r34['fixed']}/{_r34['checked']}, "
                      f"qaytarildi {_r34['sum']:,.0f}")
except Exception:
    pass


# =====================================================================
#  BOSHQA FILIALDAGI GURUHGA O'TKAZISH (2026-09-23)
#
#  Jahongir: "boshqa filialga otkizish funksiyasi bor edi oldin
#  guruhdan guruhga otkizish funksiyasi tagida shuni qoshib qoy
#  boshqa guruhga otkiza olish kerak boshqa filialdagi, tolovlari
#  ham togri bolib o'tkizilishi kerak".
#
#  Ilgari ikkita alohida amal bor edi va ikkalasi ham yarim edi:
#    * "Boshqa guruhga o'tkazish" — pulni to'g'ri qayta hisoblaydi
#      (ko'chgan kungacha eski guruh narxida, keyin yangi guruh
#      narxida), lekin boshqa filial guruhini 400 bilan rad etardi;
#    * "Boshqa filialga o'tkazish" — filialni almashtiradi, ammo
#      PULGA UMUMAN TEGMAYDI, eski guruh bog'lanishini yopmaydi
#      (o'quvchi eski guruh ro'yxatida ko'rinib turardi — bu aynan
#      2026-09-03 da guruh ko'chirishda tuzatilgan xato) va narx
#      qulfini tekshirmaydi.
#
#  Endi ikkala amal ham BITTA yo'ldan — _xb_move() — o'tadi.
#
#  PUL TARIXI. To'lov qatorida filial saqlanmaydi, hisobotlar
#  o'quvchining HOZIRGI filialiga qaraydi. Demak o'tkazilgandan keyin
#  o'tgan oylarning puli ham yangi filial hisobida ko'rinadi.
#  2026-09-23 da Jahongir buni ataylab shunday qoldirdi ("hozircha
#  shundoq qolsin"). To'lovga filial ustuni qo'shilsa — shu izoh,
#  bu yer va moliya hisobotlari birga qayta ko'riladi.
# =====================================================================
_XB_ROLES = tuple(roles.STUDENT_TRANSFER)


def _xb_closed_branches(db, user) -> list:
    """Bu xodim uchun YOPIQ filiallar: hamkor markaz (boshqa biznes)
    va test filiali. Ro'yxatda ham ko'rinmaydi, o'tkazib ham
    bo'lmaydi (2026-09-23 ko'rigi)."""
    out = set()
    for fn in ("blocked_branch_ids", "hidden_branch_ids"):
        try:
            out |= set(getattr(_CM, fn)(db, user) or [])
        except Exception:
            pass
    return list(out)


# DIQQAT: entry.py dagi `M` — bu `main`, `common` emas. main faqat bir
# qism yordamchini qayta eksport qiladi; bog'lanish va qayta hisoblash
# funksiyalari faqat common'da. Modul sifatida olamiz — shunda ular
# keyin almashtirilsa (monkey-patch) ham yangisi ishlaydi.
import common as _CM  # noqa: E402


@app.get("/api/students/{student_id}/transfer-groups")
def student_transfer_groups(student_id: int,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*_XB_ROLES))):
    """O'tkazish uchun guruhlar ro'yxati — BARCHA filiallardan.

    Filialga bog'langan xodim odatda faqat o'z filialini ko'radi
    (scope_to_branch). Aynan shuning uchun "Boshqa filialga
    o'tkazish" tugmasi administrator va filial rahbarida umuman
    chiqmasdi: ro'yxatda boshqa filial guruhi bo'lmagach, tugma ham
    yo'q edi. Bu ro'yxat ataylab filialdan tashqari, lekin ichida
    FAQAT guruh tanlash uchun kerak bo'lgan ma'lumot bor: nomi,
    filiali, ustozi, kuni/vaqti, bir dars narxi va band joylar.
    Boshqa filialning pul hisoboti yoki o'quvchilari ko'rinmaydi."""
    s = M._get_student_in_scope(db, student_id, user)
    today = roles.local_today()
    # YOPIQ FILIALLAR bu yerda ham amal qiladi: hamkor markaz (Stech)
    # boshqa biznes, test filiali esa soxta ma'lumot. Ularning
    # guruhlari boshqa hech qayerda ko'rinmaydi — bu ro'yxatda ham
    # ko'rinmasligi kerak (2026-09-23 ko'rigi).
    hide = set(_xb_closed_branches(db, user))
    rows = (db.query(models.Group)
            .order_by(models.Group.branch_id, models.Group.name).all())
    branches = {b.id: b for b in db.query(models.Branch).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    rooms = {r.id: r for r in db.query(models.Room).all()}
    out = []
    for g in rows:
        if s.group_id and g.id == s.group_id:
            continue
        if g.end_date and g.end_date < today:
            continue                       # tugagan guruh — tanlanmaydi
        if g.branch_id and g.branch_id in hide:
            continue                       # hamkor markaz / test filiali
        br = branches.get(g.branch_id)
        t = teachers.get(g.teacher_id)
        try:
            busy = _CM._active_student_count(db, g.id, exclude_student_id=s.id)
            cap = _CM._group_capacity(g, rooms)
        except Exception:
            busy, cap = 0, None
        out.append({
            "id": g.id, "name": g.name,
            "branch_id": g.branch_id,
            "branch": br.name if br else None,
            # Filialsiz guruhga o'tkazilganda filial o'zgarmaydi —
            # demak u "boshqa filial" emas (2026-09-23 ko'rigi).
            "same_branch": bool(not g.branch_id or not s.branch_id
                                or g.branch_id == s.branch_id),
            "teacher": t.full_name if t else None,
            "subject": g.subject, "level": g.level,
            "lesson_days": g.lesson_days, "lesson_time": g.lesson_time,
            "lesson_price": float(g.lesson_price or 0),
            "students": busy, "capacity": cap,
        })
    return {"rows": out, "branch_id": s.branch_id,
            "branch": s.branch.name if s.branch else None}


def _xb_move(db: Session, s, g, user, note: str = None,
             force: bool = False) -> dict:
    """Guruhga ko'chirish; guruh boshqa filialda bo'lsa filial ham.

    Guruh ko'chirishning to'liq tartibi (students.move_student_group)
    shu yerda takrorlanadi, chunki u yerdagi `_get_group_in_scope`
    boshqa filial guruhini o'tkazmaydi:
      1) sig'im/daraja tekshiruvi (force bilan o'tkazib yuborish),
      2) narx qulfi qayta ko'riladi,
      3) yangi bog'lanish ochiladi, eskisi YOPILADI (o'chirilmaydi),
      4) shu oyning hisobi qayta bo'linadi,
      5) filial almashsa — qabul qiluvchi filialga vazifa tushadi.
    """
    # MANZIL FILIALI: hamkor markaz (boshqa biznes) va test filiali
    # yopiq — o'quvchi (va uning to'lov tarixi) u yerga o'tmaydi
    # (2026-09-23 ko'rigi).
    if g.branch_id and g.branch_id in set(_xb_closed_branches(db, user)):
        raise HTTPException(
            403, "Bu filialga o'tkazib bo'lmaydi — alohida markaz")
    M._raise_if_blocked(M._check_enrolment(db, s, g), force=force)
    old_group = s.group
    old_branch_name = s.branch.name if s.branch else "—"
    old_group_name = old_group.name if old_group else None
    cross = bool(g.branch_id and s.branch_id and g.branch_id != s.branch_id)

    if not s.level:
        s.subject = s.subject or g.subject
        s.level = g.level

    # NARX QULFI (2026-09-06 auditidagi qoida): qulflangan narx faqat
    # yangi guruh narxiga teng bo'lsagina qoladi.
    try:
        _lock = getattr(s, "locked_lesson_price", None)
        _newp = float(g.lesson_price or 0)
        if _lock is not None and _newp and abs(float(_lock) - _newp) > 0.5:
            audit.log(db, user, entity="student", action="update",
                      entity_id=s.id, entity_label=s.full_name,
                      field="locked_lesson_price", old_value=_lock,
                      new_value=None, branch_id=s.branch_id,
                      note=f"Guruh almashdi ({g.name}) — narx qulfi olib "
                           f"tashlandi, yangi guruh narxi ishlaydi")
            s.locked_lesson_price = None
    except Exception:
        pass

    audit.log(db, user, entity="student", action="group_move",
              entity_id=s.id, entity_label=s.full_name, field="group",
              old_value=old_group_name, new_value=g.name,
              branch_id=s.branch_id, note=note or None)

    s.group_id = g.id
    if g.branch_id:
        s.branch_id = g.branch_id

    # BOG'LANISH: avval yangisi qo'shiladi, keyin eskisi yopiladi —
    # teskarisi qilinsa sync_primary_group() group_id ni eski guruhga
    # qaytarib yuborishi mumkin (2026-09-03).
    link = _C_CM.attach_group(db, s, g.id, user)
    if old_group is not None and old_group.id != g.id:
        _CM.detach_group(db, s, old_group.id)
    # FILIAL ALMASHSA — ESKI FILIALDAGI HAMMA GURUHDAN chiqadi
    # (2026-09-23 ko'rigi). Ilgari faqat asosiy guruh yopilardi:
    # ikki guruhli o'quvchi yangi filialga o'tsa ham eski filial
    # ro'yxatlarida, davomatida va ustoz oyligida qolib ketardi.
    if cross:
        for lk in (db.query(models.StudentGroupLink)
                   .filter(models.StudentGroupLink.student_id == s.id,
                           models.StudentGroupLink.group_id != g.id,
                           models.StudentGroupLink.active == 1).all()):
            og = db.query(models.Group).get(lk.group_id)
            if og is None or og.branch_id != g.branch_id:
                _CM.detach_group(db, s, lk.group_id)
    if link is not None:
        for other in (db.query(models.StudentGroupLink)
                      .filter(models.StudentGroupLink.student_id == s.id,
                              models.StudentGroupLink.group_id != g.id)
                      .all()):
            other.is_primary = 0
        link.is_primary = 1
    s.group_id = g.id
    db.commit()

    # MOLIYA: oy o'rtasida ko'chsa shu oyning yagona hisob qatori
    # eski/yangi guruh darslariga bo'linib qayta yoziladi.
    recharge = None
    try:
        recharge = _CM._recharge_after_move(db, s, old_group, g, user=user)
        db.commit()
    except Exception:
        db.rollback()

    task_for = None
    if cross:
        admin = _branch_admin(db, g.branch_id)
        try:
            bal = M.student_balance(db, s.id)
        except Exception:
            bal = 0
        lines = [f"O'quvchi: {s.full_name}",
                 f"Qayerdan: {old_branch_name}"
                 + (f" · {old_group_name}" if old_group_name else ""),
                 f"Guruh: {g.name}",
                 f"Balans: {bal:,.0f} so'm".replace(",", " ")]
        if recharge:
            lines.append(
                ("Shu oy hisobi qayta hisoblandi: "
                 f"{recharge.get('old', 0):,.0f} → "
                 f"{recharge.get('new', 0):,.0f} so'm").replace(",", " "))
        if note:
            lines.append(f"Izoh: {note}")
        lines.append("")
        lines.append("Kerak: o'quvchini kutib oling, dars jadvalini "
                     "tasdiqlang, ota-onasiga xabar bering.")
        task = models.Task(
            title=f"Yangi o'quvchi keldi: {s.full_name} "
                  f"({old_branch_name}dan)",
            description="\n".join(lines),
            assignee_id=admin.id if admin else None,
            branch_id=g.branch_id,
            deadline=roles.local_today() + _CM.timedelta(days=2),
            priority="high", source="manual",
            created_by=(user.full_name if user else "avtomat"))
        db.add(task)
        db.flush()
        try:
            M._ensure_public_id(db, "task", task)
        except Exception:
            pass
        audit.log(db, user, entity="student", action="group_move",
                  entity_id=s.id, entity_label=s.full_name, field="branch",
                  old_value=old_branch_name,
                  new_value=(s.branch.name if s.branch else None),
                  branch_id=s.branch_id, note=note or None)
        db.commit()
        task_for = admin.full_name if admin else None

    return {"ok": True, "group_id": g.id, "group": g.name,
            "branch_id": s.branch_id,
            "branch": s.branch.name if s.branch else None,
            "branch_changed": cross, "recharge": recharge,
            "task_for": task_for}


_xb_prev_move_group = _find_endpoint("/api/students/{student_id}/move-group",
                                     "POST")
_drop_route("/api/students/{student_id}/move-group", "POST")


@app.post("/api/students/{student_id}/move-group")
def move_student_group_v3(student_id: int, payload: schemas.StudentGroupMove,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*_XB_ROLES))):
    """Boshqa guruhga o'tkazish — endi boshqa FILIALDAGI guruhga ham.

    Shu filialdagi guruh bo'lsa eski yo'l ishlaydi (hech narsa
    o'zgarmadi). Boshqa filial guruhi tanlansa — _xb_move(): filial
    almashadi, pul qayta hisoblanadi, qabul qiluvchi filialga vazifa
    tushadi."""
    s = M._get_student_in_scope(db, student_id, user)
    if not payload.group_id:
        raise HTTPException(
            400, "Guruhdan chiqarish uchun sabab ko'rsatilishi shart — "
                 "'Guruhdan chiqarish' amalidan foydalaning")
    g = db.query(models.Group).get(int(payload.group_id))
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if g.id == s.group_id:
        raise HTTPException(400, "O'quvchi allaqachon shu guruhda")
    same = not (g.branch_id and s.branch_id and g.branch_id != s.branch_id)
    if same and _xb_prev_move_group is not None:
        return _xb_prev_move_group(student_id=student_id, payload=payload,
                                   force=force, db=db, user=user)
    return _xb_move(db, s, g, user,
                    note=getattr(payload, "note", None), force=force)


_drop_route("/api/students/{student_id}/move-branch", "POST")


@app.post("/api/students/{student_id}/move-branch")
def move_student_branch_v2(student_id: int, payload: dict,
                           force: bool = False,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*_XB_ROLES))):
    """O'quvchini boshqa filialga o'tkazadi.

    Guruh tanlansa — guruh ko'chirish bilan BIR XIL yo'ldan o'tadi
    (pul qayta hisoblanadi, eski guruh bog'lanishi yopiladi).
    Tanlanmasa — filial almashadi, eski guruhdan chiqariladi va
    yangi filial administratori guruh tanlaydi."""
    # 2026-09-23: manba filiali ham tekshiriladi. Ilgari bu yerda
    # oddiy .get() turardi — filial rahbari BOSHQA filial
    # o'quvchisini ham ko'chira olardi.
    s = M._get_student_in_scope(db, student_id, user)

    bid = payload.get("branch_id")
    if not bid:
        raise HTTPException(400, "Filial tanlanmadi")
    br = db.query(models.Branch).get(int(bid))
    if not br:
        raise HTTPException(404, "Filial topilmadi")
    if s.branch_id == br.id:
        raise HTTPException(400, "O'quvchi allaqachon shu filialda")
    note = str(payload.get("note") or "").strip() or None

    gid = payload.get("group_id")
    if gid:
        g = db.query(models.Group).get(int(gid))
        if not g:
            raise HTTPException(404, "Guruh topilmadi")
        if g.branch_id != br.id:
            raise HTTPException(400, "Bu guruh tanlangan filialda emas")
        return _xb_move(db, s, g, user, note=note, force=force)

    if br.id in set(_xb_closed_branches(db, user)):
        raise HTTPException(
            403, "Bu filialga o'tkazib bo'lmaydi — alohida markaz")

    old_branch_name = s.branch.name if s.branch else "—"
    old_group = s.group
    s.branch_id = br.id
    # AVVAL guruhlardan chiqaramiz, KEYIN group_id ni bo'shatamiz.
    # Teskarisi qilinsa detach_group() ichidagi sync_primary_group()
    # o'quvchini eski filialdagi ikkinchi guruhga qaytarib qo'yadi
    # va "guruhsiz o'tkazdim" degani yolg'on bo'lib qoladi
    # (2026-09-23 ko'rigi).
    for lk in (db.query(models.StudentGroupLink)
               .filter(models.StudentGroupLink.student_id == s.id,
                       models.StudentGroupLink.active == 1).all()):
        try:
            _CM.detach_group(db, s, lk.group_id)
        except Exception:
            pass
    s.group_id = None

    admin = _branch_admin(db, br.id)
    try:
        bal = M.student_balance(db, s.id)
    except Exception:
        bal = 0
    lines = [f"O'quvchi: {s.full_name}",
             f"Qayerdan: {old_branch_name}"
             + (f" · {old_group.name}" if old_group is not None else ""),
             "Guruh: hali tanlanmagan — guruh tanlang",
             f"Balans: {bal:,.0f} so'm".replace(",", " ")]
    if note:
        lines.append(f"Izoh: {note}")
    lines.append("")
    lines.append("Kerak: o'quvchini kutib oling, guruhini va dars "
                 "jadvalini tasdiqlang, ota-onasiga xabar bering.")
    task = models.Task(
        title=f"Yangi o'quvchi keldi: {s.full_name} ({old_branch_name}dan)",
        description="\n".join(lines),
        assignee_id=admin.id if admin else None,
        branch_id=br.id,
        deadline=roles.local_today() + _CM.timedelta(days=2),
        priority="high", source="manual",
        created_by=user.full_name)
    db.add(task)
    db.flush()
    try:
        M._ensure_public_id(db, "task", task)
    except Exception:
        pass
    audit.log(db, user, entity="student", action="group_move",
              entity_id=s.id, entity_label=s.full_name, field="branch",
              old_value=old_branch_name, new_value=br.name,
              branch_id=br.id, note=note)
    db.commit()
    return {"ok": True, "branch_id": br.id, "branch": br.name,
            "group_id": None, "group": None,
            "task_for": admin.full_name if admin else None}


# =====================================================================
#  SXEMA MUHRI — ENG OXIRIDA (2026-09-11)
#
#  Shu qatorga yetib kelganda entry.py o'zining HAMMA jadvalini
#  (placement_sessions, library_items, pd_videos, staff_grades ...)
#  e'lon qilib bo'lgan bo'ladi. Ya'ni Base.metadata endi TO'LIQ.
#  seal_schema() yetishmayotgan jadval/ustunlarni oxirgi marta
#  tekshiradi va shundan keyingina shtampni yozadi.
#
#  Nega shunday: bugun placement_sessions ga ikkita yangi ustun
#  qo'shdim, lekin shtampni main.py import paytida yozilgani uchun
#  ular jonli bazada paydo bo'lmadi va Lidlar sahifasi 500 qaytardi.
#  Shtamp oxirida yozilsa, bunday bo'lishi mumkin emas.
try:
    from common import seal_schema as _seal_schema
    _seal_schema()
except Exception:
    pass



# =====================================================================
#  DIAGNOSTIKA NATIJALARINI JONY SCHOOL'GA EKSPORT  (_PX_*, 2026-09-26)
#
#  Jahongir: "Jony Academy test filialida ... diagnostik testni berishga
#  majbur boldim 11-sinflarga lid qilib korgizdim ularni natijalarini
#  ham qoshib qo'y ozing endi topib Jony 360ga".
#
#  Ikki tizim alohida bazada. Parol/ulanish ko'chirilmaydi: JonyOS
#  tugallangan diagnostika natijalarini JSON qilib beradi (Lidlar →
#  Diagnostika → "Jony School'ga eksport"), Jony School o'sha faylni
#  o'qib, o'quvchini ismi bo'yicha topadi va Jony 360 mavzu
#  natijalariga yozadi. Hech narsa o'chirilmaydi.
# =====================================================================
@app.get("/api/placement/export")
def pt_export(days: int = 30, branch_id: int | None = None,
              db: Session = Depends(get_db),
              user=Depends(require_role(*_PT_ROLES))):
    """Oxirgi N kundagi TUGALLANGAN diagnostikalar — Jony School importi
    uchun. Natija bo'limlar (grammatika/lug'at/reading/listening) va
    grammatika mavzulari kesimida."""
    since = _pt_now() - _pt_td(days=max(1, min(365, int(days or 30))))
    q = (db.query(_PTS).filter(_PTS.status == "done",
                               _PTS.finished_at >= since))
    if branch_id:
        q = q.filter(_PTS.branch_id == int(branch_id))
    rows = []
    for s in q.order_by(_PTS.finished_at.desc()).limit(500).all():
        r = _pt_result(s)
        rows.append({
            "session_id": s.id, "lead_id": s.lead_id, "name": s.name,
            "phone": s.phone, "branch_id": s.branch_id,
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            "level": r.get("level"), "unit": r.get("unit"),
            "overall": r.get("overall"), "score": r.get("score"),
            "total": r.get("total"),
            "skills": [{"key": x["key"], "level": x.get("level"),
                        "pct": x.get("pct"), "n": x.get("n")}
                       for x in r.get("skills") or []],
            "topics": [{"level": t["level"], "unit": t["unit"],
                        "topic": t["topic"], "ok": t["ok"], "n": t["n"],
                        "pct": t["pct"]} for t in r.get("topics") or []],
        })
    return {"source": "jonyos", "kind": "placement",
            "exported_at": _pt_now().isoformat(), "days": days,
            "count": len(rows), "rows": rows}


# OY YOPILISHI VA P&L (2026-10-02) — alohida faylda
import month_close  # noqa: E402,F401

# WEB PUSH — telefonga bildirishnoma (2026-10-03)
import push  # noqa: E402,F401

# Imtihon natijasi va xatolar tahlili — o'quvchiga (2026-10-03)
import exam_review  # noqa: E402,F401
