"""Auto-extracted from main.py during refactor (split-main). Domain: exams."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
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
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()

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

def _exam_in_scope(db: Session, exam_id: int, user: models.User) -> models.Exam:
    exam = db.query(models.Exam).get(exam_id)
    if not exam:
        raise HTTPException(404, "Imtihon topilmadi")
    _get_group_in_scope(db, exam.group_id, user)
    return exam

@router.get("/api/exams/{exam_id}", response_model=schemas.ExamDetail)
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

@router.delete("/api/exams/{exam_id}")
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

@router.put("/api/exams/{exam_id}/results", response_model=schemas.ExamDetail)
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
    # Oylik uchun: kim o'tkazgani hali yozilmagan bo'lsa, natijani
    # kiritayotgan examiner o'tkazgan hisoblanadi.
    if not exam.examiner_id and user.role in (
            roles.EXAMINER, roles.HEAD_EXAMINER):
        exam.examiner_id = user.id
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

    # AVTOMAT SERTIFIKAT: daraja yakuniy testi ("end") dan o'tgan har
    # bir o'quvchiga tugatganlik sertifikati yoziladi — StudentDetail
    # -> Sertifikatlar bo'limidan yuklab olinadi. Bir daraja uchun
    # bitta sertifikat: qayta topshirsa dublikat ochilmaydi.
    if exam.kind == "end":
        _g = db.query(models.Group).get(exam.group_id)
        _lvl = ((_g.level or "").strip() or None) if _g else None
        _lvl_label = _lvl or (exam.title or "Kurs yakuni")
        for _r in exam.results:
            if _r.absent or _r.percent is None:
                continue
            if _r.percent < roles.LEVEL_PASS_PERCENT:
                continue
            _dup = (db.query(models.Certificate)
                    .filter(models.Certificate.student_id == _r.student_id,
                            models.Certificate.kind == "level",
                            models.Certificate.level == _lvl_label)
                    .first())
            if _dup:
                continue
            db.add(models.Certificate(
                student_id=_r.student_id, kind="level",
                level=_lvl_label, score=_r.percent,
                note=(f"{_lvl_label} darajasi yakuniy testi — "
                      f"{_r.percent}% bilan o'tdi"),
                created_by="JonyOS avtomat"))
        db.commit()

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

@router.get("/api/exam-coin-rules", response_model=List[schemas.ExamCoinRuleOut])
def list_coin_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return db.query(models.ExamCoinRule).order_by(
        models.ExamCoinRule.min_percent.desc()).all()

@router.put("/api/exam-coin-rules", response_model=List[schemas.ExamCoinRuleOut])
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

def _seed_rubrics(db: Session) -> None:
    have = {r.key for r in db.query(models.LessonRubric).all()}
    added = False
    for key, name, desc in roles.RUBRICS:
        if key in have:
            continue
        db.add(models.LessonRubric(key=key, name=name, description=desc,
                                   is_active=1))
        added = True
    if added:
        db.commit()

    for key, items in roles.RUBRIC_ITEMS.items():
        existing = (db.query(models.RubricCriterion)
                    .filter(models.RubricCriterion.rubric_key == key).count())
        if existing:
            continue          # HR tahrirlagan bo'lishi mumkin — tegmaymiz
        for no, text, points in items:
            db.add(models.RubricCriterion(
                rubric_key=key, order_no=no, text=text, points=points,
                is_active=1))
        db.commit()

@router.get("/api/rubrics")
def list_rubrics(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.OBSERVATION_ACCESS)),
):
    """Baholash jadvallari va ularning mezonlari."""
    _seed_rubrics(db)
    out = []
    for r in (db.query(models.LessonRubric)
              .order_by(models.LessonRubric.id).all()):
        items = _criteria(db, r.key)
        out.append({
            "key": r.key, "name": r.name, "description": r.description,
            "is_active": bool(r.is_active),
            "max_total": round(sum(c.points or 0 for c in items), 1),
            "criteria": [{
                "id": c.id, "no": c.order_no, "text": c.text,
                "points": c.points or 0,
            } for c in items],
        })
    return {
        "rows": out,
        "targets": [{"key": k, "label": lbl}
                    for k, lbl in roles.OBSERVATION_TARGETS],
        "pass_score": roles.TEACHER_MIN_SKILL,
        "head_score": roles.HEAD_MIN_SKILL,
        "can_edit": user.role in roles.GRADE_ADMIN,
        "hint": ("Faqat \"Fakt\" ustunini to'ldirasiz — jami va foiz o'zi "
                 f"hisoblanadi. Ustozlikni boshlash uchun "
                 f"{round(roles.TEACHER_MIN_SKILL)}+ ball, Head teacher "
                 f"uchun {round(roles.HEAD_MIN_SKILL)}+ ball kerak."),
    }

@router.put("/api/rubrics/criteria/{cid}")
def update_criterion(
    cid: int,
    payload: schemas.CriterionUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    c = db.query(models.RubricCriterion).get(cid)
    if not c:
        raise HTTPException(404, "Mezon topilmadi")
    given = payload.model_dump(exclude_unset=True)
    for k, v in given.items():
        setattr(c, k, 1 if k == "is_active" and v else
                (0 if k == "is_active" else v))
    db.commit()
    audit.log(db, user, entity="rubric", action="update", entity_id=c.id,
              entity_label=c.text[:60], new_value=str(given),
              note="Baholash mezoni o'zgartirildi")
    db.commit()
    items = _criteria(db, c.rubric_key)
    return {"ok": True,
            "max_total": round(sum(x.points or 0 for x in items), 1)}

@router.post("/api/rubrics/criteria")
def add_criterion(
    payload: schemas.CriterionCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    items = _criteria(db, payload.rubric_key)
    c = models.RubricCriterion(
        rubric_key=payload.rubric_key, text=payload.text,
        points=payload.points,
        order_no=(max([x.order_no or 0 for x in items], default=0) + 1),
        is_active=1)
    db.add(c)
    db.commit()
    return {"ok": True, "id": c.id}

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

@router.get("/api/exam-orders")
def exam_orders_queue(status: str | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.EXAM_ORDER_ACCEPT))):
    """Examiner navbati — FAQAT o'z filialidagi so'rovlar.

    Examiner boshlig'i va asoschi hammasini ko'radi."""
    q = db.query(models.ExamOrder)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.ExamOrder.branch_id == user.branch_id)
    if status:
        q = q.filter(models.ExamOrder.status == status)
    rows = q.order_by(models.ExamOrder.date, models.ExamOrder.id).limit(
        200).all()
    out = [_exam_order_out(db, o) for o in rows]
    today = roles.local_today()
    return {
        "rows": out,
        "new": sum(1 for r in out if r["status"] == "new"),
        "accepted": sum(1 for r in out if r["status"] == "accepted"),
        # Bugun va ertaga bo'ladigan, hali qabul qilinmaganlar
        "urgent": [r for r in out if r["status"] == "new" and r["date"]
                   and r["date"] <= (today + timedelta(days=1)).isoformat()],
        **_exam_order_form(db, user),
        "hint": ("Qabul qilinganda imtihon avtomat yaratiladi va "
                 "ustozga sizning ismingiz ko'rinadi."),
    }

@router.post("/api/exam-orders/{oid}/accept")
def exam_order_accept(oid: int, payload: schemas.ExamOrderDecision,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.EXAM_ORDER_ACCEPT))):
    """Examiner buyurtmani o'ziga oladi va imtihon yaratiladi."""
    o = db.query(models.ExamOrder).get(oid)
    if not o:
        raise HTTPException(404, "Buyurtma topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id \
            and o.branch_id != user.branch_id:
        raise HTTPException(403, "Bu buyurtma boshqa filialga tegishli")
    if o.status == "accepted":
        who = db.query(models.User).get(o.accepted_by)
        raise HTTPException(
            400, f"Buyurtmani allaqachon "
                 f"{who.full_name if who else 'boshqa examiner'} qabul qilgan")
    if o.status != "new":
        raise HTTPException(400, "Bu buyurtma yopilgan")

    g = db.query(models.Group).get(o.group_id)
    o.status = "accepted"
    o.accepted_by = user.id
    o.accepted_at = datetime.utcnow()
    o.decision_note = payload.note

    # AVTOMAT: qabul qilinishi bilan imtihon tayyor bo'ladi —
    # examiner alohida "imtihon yarat" tugmasini bosmaydi
    ex = models.Exam(
        group_id=o.group_id, kind=o.kind, unit_no=o.unit_no,
        title=roles.exam_title(o.kind, o.unit_no),
        date=o.date, status="approved",
        approved_by=user.full_name, approved_at=roles.local_today(),
        note=f"Buyurtma {o.public_id}",
        created_by=user.full_name,
        examiner_id=user.id)
    db.add(ex); db.flush()
    o.exam_id = ex.id
    db.commit(); db.refresh(o)

    # Ustozga xabar — kim qabul qilgani ko'rinsin
    out = _exam_order_out(db, o)
    if o.requested_by:
        _hr_task_for(db, o.requested_by,
                     title=f"Imtihon tasdiqlandi {o.public_id}",
                     body=out["message"],
                     branch_id=o.branch_id,
                     days=max(1, (o.date - roles.local_today()).days))
        db.commit()

    audit.log(db, user, entity="exam_order", action="accept",
              entity_id=o.id, entity_label=g.name if g else None,
              branch_id=o.branch_id, new_value=user.full_name,
              note=payload.note, commit=True)
    return out

@router.post("/api/exam-orders/{oid}/reject")
def exam_order_reject(oid: int, payload: schemas.ExamOrderDecision,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.EXAM_ORDER_ACCEPT))):
    o = db.query(models.ExamOrder).get(oid)
    if not o:
        raise HTTPException(404, "Buyurtma topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id \
            and o.branch_id != user.branch_id:
        raise HTTPException(403, "Bu buyurtma boshqa filialga tegishli")
    if o.status not in ("new", "accepted"):
        raise HTTPException(400, "Bu buyurtma yopilgan")
    # Rad etish sababsiz bo'lmaydi: ustoz nima qilishini bilishi kerak
    if roles.EXAM_ORDER_REJECT_NEEDS_NOTE and not (payload.note
                                                   or payload.reason):
        raise HTTPException(400, "Rad etish sababini yozing")

    o.status = "rejected"
    o.reject_reason = payload.reason
    o.decision_note = payload.note
    o.accepted_by = user.id
    o.accepted_at = datetime.utcnow()
    db.commit(); db.refresh(o)

    out = _exam_order_out(db, o)
    if o.requested_by:
        why = out["reject_reason_label"] or payload.note or "sabab ko'rsatilmagan"
        _hr_task_for(db, o.requested_by,
                     title=f"Imtihon buyurtmasi rad etildi {o.public_id}",
                     body=out["message"] + f"\n\nSabab: {why}"
                          + (f"\nIzoh: {payload.note}" if payload.note else ""),
                     branch_id=o.branch_id, days=1)
        db.commit()

    audit.log(db, user, entity="exam_order", action="reject",
              entity_id=o.id, branch_id=o.branch_id,
              new_value=payload.reason, note=payload.note, commit=True)
    return out

@router.post("/api/exam-orders/{oid}/done")
def exam_order_done(oid: int, payload: schemas.ExamOrderDecision,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_ORDER_ACCEPT))):
    """Imtihon o'tkazildi."""
    o = db.query(models.ExamOrder).get(oid)
    if not o:
        raise HTTPException(404, "Buyurtma topilmadi")
    if o.status != "accepted":
        raise HTTPException(400, "Avval buyurtma qabul qilinishi kerak")
    o.status = "done"
    if payload.note:
        o.decision_note = payload.note
    ex = db.query(models.Exam).get(o.exam_id) if o.exam_id else None
    if ex and ex.status == "approved":
        ex.status = "done"
    db.commit()
    audit.log(db, user, entity="exam_order", action="done",
              entity_id=o.id, branch_id=o.branch_id, commit=True)
    return _exam_order_out(db, o)

@router.post("/api/exams/{exam_id}/penalty")
def set_exam_penalty(exam_id: int, payload: schemas.ExamPenaltyIn,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(
                         *roles.EXAMINER_PENALTY_SET))):
    """Bo'lim boshlig'i imtihonga jarima belgilaydi: LC UP, coin,
    jadvaldan kechikish (soat). Qayta bosilsa - eski qiymat almashadi."""
    exam = db.query(models.Exam).get(exam_id)
    if not exam:
        raise HTTPException(404, "Imtihon topilmadi")
    if payload.delay_hours < 0 or payload.delay_hours > 24:
        raise HTTPException(400, "Kechikish 0-24 soat oralig'ida bo'lsin")
    exam.penalty_lc_up = 1 if payload.lc_up else 0
    exam.penalty_coin = 1 if payload.coin else 0
    exam.penalty_delay_hours = payload.delay_hours or 0
    exam.penalty_note = payload.note
    exam.penalty_by = user.full_name
    db.commit()
    g = db.query(models.Group).get(exam.group_id)
    audit.log(db, user, entity="exam", action="penalty",
              entity_id=exam.id, entity_label=g.name if g else None,
              new_value=(f"LC UP: {'ha' if payload.lc_up else 'yo`q'}, "
                         f"Coin: {'ha' if payload.coin else 'yo`q'}, "
                         f"kechikish: {payload.delay_hours or 0} soat"),
              note=payload.note, commit=True)
    return {"ok": True}

