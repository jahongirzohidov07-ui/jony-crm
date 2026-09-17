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

def _counted_ids(db: Session, exam: models.Exam,
                 student_ids: list) -> set:
    """Imtihon kunigacha shu guruhda KAMIDA 1 ta yo'qlamasi bor
    o'quvchilar. Qolganlari (endi kelganlar) natijada ko'rinadi,
    lekin umumiy o'rtachaga va coinga kirmaydi (Jahongir:
    "Kelishiga imthon bo'lib qolgan o'quvchilar ham umumiy ballga
    kiritilmaydi... Ustoz dars o'tsa, yoqlama qoysa hech bo'lmasa
    1ta va undan keyin imthonga kirganlar umumiyga hisoblanaveradi")."""
    if not student_ids:
        return set()
    q = (db.query(models.Attendance.student_id)
         .join(models.Lesson,
               models.Lesson.id == models.Attendance.lesson_id)
         .filter(models.Lesson.group_id == exam.group_id,
                 models.Attendance.student_id.in_(student_ids)))
    if exam.date:
        q = q.filter(models.Lesson.date <= exam.date)
    return {sid for (sid,) in q.distinct().all()}


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
    user=Depends(require_role(*roles.EXAM_EDIT)),
):
    """Imtihon o'chirilsa, u bergan coinlar ham qaytariladi."""
    exam = _exam_in_scope(db, exam_id, user)
    # Qayta imtihonlari shu testga bog'langan — bog'lanish uziladi
    if db.query(models.Exam).filter(
            models.Exam.retake_of_id == exam.id).count():
        (db.query(models.Exam)
         .filter(models.Exam.retake_of_id == exam.id)
         .update({models.Exam.retake_of_id: None},
                 synchronize_session=False))
    label = exam.title or roles.exam_title(exam.kind, exam.unit_no)
    n_res = len(exam.results)
    ex_date = exam.date.isoformat() if exam.date else ""
    grp = db.query(models.Group).get(exam.group_id)
    for r in exam.results:
        _drop_coin_entry(db, "exam", r.id)
    db.delete(exam)
    db.commit()
    audit.log(db, user, entity="exam", action="delete", entity_id=exam_id,
              entity_label=f"{label} — {grp.name if grp else ''}".strip(" —"),
              branch_id=grp.branch_id if grp else None,
              old_value=f"{ex_date}, "
                        f"{n_res} ta natija",
              commit=True)
    return {"ok": True}


def _free_student_ids(db: Session, student_ids: list) -> set:
    """100% chegirmali o'quvchilar — coin olmaydi (save_exam_results
    bilan bir xil qoida)."""
    out = set()
    if student_ids:
        for d in (db.query(models.Discount)
                  .filter(models.Discount.student_id.in_(student_ids),
                          models.Discount.status == "active",
                          models.Discount.percent >= 100).all()):
            if _discount_alive(d):
                out.add(d.student_id)
    return out


@router.put("/api/exams/{exam_id}", response_model=schemas.ExamOut)
def update_exam(
    exam_id: int,
    payload: schemas.ExamUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_EDIT)),
):
    """Imtihonni tahrirlash (2026-09-17): nomi, sanasi, turi, unit
    raqami va maksimal ball. Maksimal ball o'zgarsa kiritilgan
    natijalarning foizi va coini QAYTA hisoblanadi."""
    exam = _exam_in_scope(db, exam_id, user)
    data = payload.model_dump(exclude_unset=True)
    scored = [r for r in exam.results if not r.absent
              and (r.score is not None or r.band is not None)]

    new_kind = data.get("kind", exam.kind)
    if new_kind not in roles.EXAM_KINDS:
        raise HTTPException(400, "Noto'g'ri test turi")
    if new_kind != exam.kind and scored and \
            ("mock" in (new_kind, exam.kind)):
        raise HTTPException(
            400, "Natija kiritilgan testni Mock'ga (yoki Mock'dan) "
                 "o'tkazib bo'lmaydi — baholash usuli boshqa")
    new_unit = data.get("unit_no", exam.unit_no)
    if new_kind == "unit":
        if not new_unit or not (1 <= new_unit <= roles.UNIT_COUNT):
            raise HTTPException(
                400, f"Unit raqami 1-{roles.UNIT_COUNT} oralig'ida bo'lishi kerak")
    else:
        new_unit = None
    new_max = data.get("max_score", exam.max_score)
    if new_kind == "mock":
        new_max = None
    elif not new_max or new_max <= 0:
        raise HTTPException(400, "Maksimal ballni kiriting")
    if new_max is not None:
        over = [r for r in scored if r.score is not None and r.score > new_max]
        if over:
            raise HTTPException(
                400, f"{len(over)} ta o'quvchining bali {new_max:g} dan "
                     f"yuqori — avval natijalarni tuzating")
    new_date = data.get("date", exam.date)
    if not new_date:
        raise HTTPException(400, "Sanani kiriting")

    changes = {}
    for f, v in (("kind", new_kind), ("unit_no", new_unit),
                 ("title", (data.get("title", exam.title) or None)),
                 ("date", new_date), ("max_score", new_max)):
        if getattr(exam, f) != v:
            changes[f] = v
    if not changes:
        return _exam_summary(db, exam)
    audit.log_changes(db, user, entity="exam", obj=exam, changes=changes,
                      label_attr="title",
                      note=roles.exam_title(exam.kind, exam.unit_no))
    for f, v in changes.items():
        setattr(exam, f, v)

    # Maksimal ball yoki sana o'zgardi — foiz, hisobga kirishi (yo'qlama
    # sanagacha sanaladi) va coin qayta hisoblanadi
    if ("max_score" in changes or "date" in changes) and new_max:
        free = _free_student_ids(db, [r.student_id for r in scored])
        counted = _counted_ids(db, exam, [r.student_id for r in exam.results])
        for r in exam.results:
            r.counted = 1 if r.student_id in counted else 0
        for r in scored:
            if r.score is None:
                continue
            r.percent = round(r.score / new_max * 100, 1)
            if not r.counted or r.student_id in free:
                r.coins = 0
                _drop_coin_entry(db, "exam", r.id)
                continue
            r.coins = _coins_for_percent(db, r.percent, exam.kind)
            _sync_coin_entry(
                db, student_id=r.student_id, source="exam", ref_id=r.id,
                amount=r.coins,
                note=f"{roles.EXAM_KIND_LABELS.get(exam.kind, exam.kind)}"
                     f" - {r.percent}%",
                created_by=user.full_name,
            )
    db.commit()
    db.refresh(exam)
    return _exam_summary(db, exam)

@router.put("/api/exams/{exam_id}/results", response_model=schemas.ExamDetail)
def save_exam_results(
    exam_id: int,
    payload: schemas.ExamScoreBulk,
    db: Session = Depends(get_db),
    # Ustoz/support natija KIRITA olmaydi - baholash examinerniki
    # (Jahongir). Ko'rish (get_exam) ustozga qoladi.
    user=Depends(require_role(*[r for r in roles.TEACHING_ACCESS
                                if r not in (roles.TEACHER,
                                             roles.SUPPORT_TEACHER)])),
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
    has_lesson = _counted_ids(db, exam, [m.student_id
                                         for m in payload.marks])
    # 100% chegirmada o'qiydiganlar: baholanadi, natijasi ko'rinadi,
    # lekin coin BERILMAYDI ham YECHILMAYDI (Jahongir, 2026-08-11).
    # DIQQAT: _student_discount_percent 50% da kesiladi (umumiy cap),
    # shuning uchun bu yerda chegirma yozuvlarining O'ZI tekshiriladi:
    # faol va muddati o'tmagan percent>=100 yozuv = grant o'quvchi.
    _free_ids = set()
    _ids_ = [m.student_id for m in payload.marks]
    if _ids_:
        for _d in (db.query(models.Discount)
                   .filter(models.Discount.student_id.in_(_ids_),
                           models.Discount.status == "active",
                           models.Discount.percent >= 100).all()):
            if _discount_alive(_d):
                _free_ids.add(_d.student_id)

    for m in payload.marks:
        row = existing.get(m.student_id)
        if row is None:
            row = models.ExamResult(exam_id=exam.id, student_id=m.student_id,
                                    created_by=user.full_name)
            db.add(row)
            db.flush()

        row.absent = 1 if m.absent else 0
        row.note = m.note
        row.counted = 1 if m.student_id in has_lesson else 0

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

        if not row.counted or m.student_id in _free_ids:
            # Endi kelgan o'quvchi YOKI 100% chegirmali: natija
            # ko'rinadi, lekin coin berilmaydi/yechilmaydi
            row.coins = 0
            _drop_coin_entry(db, "exam", row.id)
            continue
        row.coins = _coins_for_percent(db, row.percent, exam.kind)
        _sync_coin_entry(
            db, student_id=m.student_id, source="exam", ref_id=row.id,
            amount=row.coins,
            note=f"{roles.EXAM_KIND_LABELS.get(exam.kind, exam.kind)}"
                 f" - {row.percent}%",
            created_by=user.full_name,
        )

    # Telegram: "test natijalari chiqdi" xabari faqat BIRINCHI marta
    # natija kiritilganda yuborilishi kerak (2026-08-09, Jahongir
    # so'radi) — status hali "approved" bo'lsa, demak bu shu test
    # uchun birinchi save_exam_results() chaqiruvi; keyinroq ustoz
    # bitta bahoni tuzatsa (status allaqachon "done"), qayta xabar
    # ketmaydi.
    was_first_entry = exam.status == "approved"
    if exam.status == "approved":
        exam.status = "done"
    db.commit()

    if was_first_entry and notify.enabled():
        try:
            title = exam.title or roles.exam_title(exam.kind, exam.unit_no)
            for r in exam.results:
                if r.absent:
                    continue
                st = db.query(models.Student).get(r.student_id)
                if st is None or not st.telegram_chat_id:
                    continue
                if r.band is not None:
                    result_desc = f"Band {r.band:g}"
                elif exam.max_score:
                    result_desc = (f"{(r.score or 0):g}/{exam.max_score:g} "
                                   f"({r.percent}%)")
                else:
                    result_desc = f"{(r.score or 0):g}"
                notify.send(
                    st.telegram_chat_id,
                    f"📊 Test natijasi chiqdi\n{st.full_name}\n"
                    f"{title}: {result_desc}")
        except Exception:
            pass

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
        # O'TISH BALLI (2026-09-10): imtihonda muhrlangan bo'lsa —
        # o'sha. Eski testlarda maydon yo'q edi, ular avvalgidek
        # LEVEL_PASS_PERCENT bilan hisoblanadi (tarix o'zgarmaydi).
        _need = roles.exam_pass_percent(exam, roles.LEVEL_PASS_PERCENT)
        for _r in exam.results:
            if _r.absent or _r.percent is None:
                continue
            if _need is not None and _r.percent < _need:
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

@router.put("/api/exams/{exam_id}/retake", response_model=schemas.ExamDetail)
def save_exam_retake(
    exam_id: int,
    payload: schemas.ExamRetakeIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*[r for r in roles.TEACHING_ACCESS
                                if r not in (roles.TEACHER,
                                             roles.SUPPORT_TEACHER)])),
):
    """RETAKE - examiner o'quvchidan qayta topshirig'ini oladi.

    Jahongir: "examdan keyin o'quvchidan examiner retake olinishi
    mumkin, va retake olinganligi va birinchi balli korinib tursin,
    retake uchun coin umuman hisoblanmasin. Retake foizi umumiyga
    ham hisoblanmaydi".

    Birinchi ball/foizga TEGILMAYDI, coin yozilmaydi, o'rtacha
    o'zgarmaydi - faqat retake ustunlari to'ldiriladi."""
    exam = _exam_in_scope(db, exam_id, user)
    if exam.status == "cancelled":
        raise HTTPException(400, "Bekor qilingan testga retake yozilmaydi")
    row = (db.query(models.ExamResult)
           .filter(models.ExamResult.exam_id == exam.id,
                   models.ExamResult.student_id == payload.student_id)
           .first())
    if row is None:
        raise HTTPException(
            404, "Avval asosiy natija kiritilishi kerak - retake "
                 "birinchi ballning ustiga yoziladi")

    if payload.remove:
        row.retake_score = None
        row.retake_band = None
        row.retake_percent = None
        row.retake_at = None
        row.retake_by = None
    elif exam.kind == "mock":
        if payload.band is None or not (0 <= payload.band
                                        <= roles.MOCK_MAX_BAND):
            raise HTTPException(400, "Band 0-9 oralig'ida bo'lishi kerak")
        row.retake_band = payload.band
        row.retake_score = None
        row.retake_percent = round(
            payload.band / roles.MOCK_MAX_BAND * 100, 1)
        row.retake_at = roles.local_today()
        row.retake_by = user.full_name
    else:
        bad = (payload.score is None or payload.score < 0
               or payload.score > (exam.max_score or 0))
        if bad:
            raise HTTPException(
                400, f"Ball 0 va {exam.max_score} oralig'ida bo'lishi kerak")
        row.retake_score = payload.score
        row.retake_band = None
        row.retake_percent = round(
            payload.score / exam.max_score * 100, 1)
        row.retake_at = roles.local_today()
        row.retake_by = user.full_name
    db.commit()

    st = db.query(models.Student).get(payload.student_id)
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=st.full_name if st else None, field="retake",
              new_value=row.retake_percent,
              note=("Retake o'chirildi" if payload.remove
                    else f"Retake: {row.retake_percent}% (coin yo'q, "
                         "o'rtachaga kirmaydi)"),
              commit=True)

    base = _exam_summary(db, exam)
    students = _group_students(db, exam.group_id)
    return schemas.ExamDetail(
        **base.model_dump(),
        results=[schemas.ExamResultOut.model_validate(r)
                 for r in exam.results],
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
    )


# =====================================================================
#  O'TISH BALLI — TEST TURI BO'YICHA (2026-09-10)
# =====================================================================
#  Jahongir: "Maksimal ball bor o'tish balli yo'qku" -> "test turi
#  boyivha sozlamalarda bir marta, foizda olchanadi, 65% unit testda
#  60% esa mid va end courselarda".
#
#  Mock ro'yxatda yo'q: u IELTS band bilan baholanadi.
_PASS_KINDS = [k for k in roles.EXAM_KINDS if k != "mock"]


def _pass_rules(db: Session):
    rows = {r.kind: r for r in db.query(models.ExamPassRule).all()}
    out = []
    for k in _PASS_KINDS:
        r = rows.get(k)
        out.append(schemas.ExamPassRuleOut(
            id=r.id if r else 0, kind=k,
            percent=(r.percent if r
                     else roles.DEFAULT_EXAM_PASS.get(k, 60.0)),
            label=roles.EXAM_KIND_LABELS.get(k, k)))
    return out


@router.get("/api/exam-pass-rules",
            response_model=List[schemas.ExamPassRuleOut])
def list_pass_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return _pass_rules(db)


@router.put("/api/exam-pass-rules",
            response_model=List[schemas.ExamPassRuleOut])
def replace_pass_rules(
    payload: List[schemas.ExamPassRuleIn],
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """O'tish ballini turlar bo'yicha saqlaydi.

    ALLAQACHON O'TKAZILGAN testlarga ta'sir QILMAYDI: har imtihon o'z
    o'tish ballini yaratilgan paytda muhrlab oladi. Bu yerdagi raqam
    faqat BUNDAN KEYIN ochiladigan testlar uchun."""
    for r in payload:
        if r.kind not in _PASS_KINDS:
            raise HTTPException(
                400, "O'tish balli faqat Unit / Mid / End uchun "
                     "belgilanadi (Mock IELTS band bilan baholanadi)")
        if not (0 < r.percent <= 100):
            raise HTTPException(400, "O'tish balli 1-100% oralig'ida "
                                     "bo'lishi kerak")
    for r in payload:
        row = (db.query(models.ExamPassRule)
               .filter(models.ExamPassRule.kind == r.kind).first())
        if row is None:
            row = models.ExamPassRule(kind=r.kind, percent=r.percent)
            db.add(row)
        else:
            row.percent = r.percent
        row.updated_by = user.full_name
        row.updated_at = datetime.utcnow()
    db.commit()
    audit.log(db, user, entity="exam_pass_rule", action="update",
              note="; ".join(f"{r.kind}={r.percent}%" for r in payload),
              commit=True)
    return _pass_rules(db)


@router.get("/api/exam-coin-rules", response_model=List[schemas.ExamCoinRuleOut])
def list_coin_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return (db.query(models.ExamCoinRule)
            .filter(models.ExamCoinRule.min_percent >= 0)
            .order_by(models.ExamCoinRule.min_percent.desc()).all())

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
        # Manfiy coin RUXSAT: past natija coin yechadi (Jahongir
        # shkalasi, 2026-08-11)
    db.query(models.ExamCoinRule).filter(
        models.ExamCoinRule.min_percent >= 0).delete(
        synchronize_session=False)
    for r in payload:
        db.add(models.ExamCoinRule(min_percent=r.min_percent, coins=r.coins,
                                   kind=r.kind))
    db.commit()
    return (db.query(models.ExamCoinRule)
            .filter(models.ExamCoinRule.min_percent >= 0)
            .order_by(models.ExamCoinRule.min_percent.desc()).all())

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
    # IKKI FILIALLI EXAMINER (2026-08-10, Jahongir: "qabul qilinishi
    # kerak bo'lgan imtihonlar ko'rinmayapti deyabdi examinerlar").
    # Ilgari faqat ASOSIY filial tekshirilardi — ikki filialda
    # ishlaydigan examiner ikkinchi filialdagi so'rovni umuman
    # ko'rmasdi, ro'yxat bo'sh chiqardi. Qabul qilish (accept/reject)
    # allaqachon barcha filiallarni hisobga olardi, RO'YXAT esa yo'q —
    # ya'ni examiner qabul qila oladigan so'rovni ko'ra olmasdi.
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.ExamOrder.branch_id.in_(
            _user_branch_ids(db, user) or [-1]))
    # SUKUT BO'YICHA FAQAT OCHIQ SO'ROVLAR (2026-09-07, Jahongir:
    # "bo'lingan testlarni betdan o'chirsa bo'ladimi, yangi testlar
    # tepada emas paaastda ko'p ketarkan, noqulay bo'lyapti").
    # HECH NARSA O'CHIRILMAYDI — o'tkazilgan/rad etilgan so'rovlar
    # bazada qoladi va "O'tkazildi" filtri yoki "Barchasi" bilan
    # ochiladi. Ro'yxat esa kundalik ishga kerakli qismini
    # ko'rsatadi: yangi va qabul qilinganlar.
    if status == "all":
        pass
    elif status:
        q = q.filter(models.ExamOrder.status == status)
    else:
        q = q.filter(models.ExamOrder.status.in_(roles.EXAM_ORDER_OPEN))
    rows = q.order_by(models.ExamOrder.date, models.ExamOrder.id).limit(
        200).all()
    out = [_exam_order_out(db, o) for o in rows]
    today = roles.local_today()

    # TARTIB: YANGI SO'ROVLAR ENG TEPADA (2026-09-07).
    # Ilgari ro'yxat faqat sana bo'yicha o'sish tartibida edi —
    # eski, allaqachon yopilgan so'rovlar tepani egallab, yangi
    # tushgan so'rov pastda qolib ketardi.
    #   1) yangi (qabul qilinmagan) — sanasi yaqinlari birinchi
    #      (bugun/ertaga bo'ladigani eng tepada);
    #   2) qabul qilinganlar — sanasi yaqinlari birinchi;
    #   3) yopilganlar (o'tkazildi, rad etildi, bekor) — eng
    #      yangisi birinchi.
    _rank = {"new": 0, "accepted": 1}
    def _sort_key(r):
        grp = _rank.get(r["status"], 2)
        d = r.get("date") or ""
        if grp == 2:
            # yopilganlar: eng yangisi tepada (sana teskari)
            return (grp, tuple(-ord(c) for c in d), -r["id"])
        return (grp, tuple(ord(c) for c in d), r["id"])
    out.sort(key=_sort_key)

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
    if not _in_user_branches(db, user, o.branch_id):
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
    # O'tish balli sozlamadan olinib, shu imtihonda muhrlanadi
    # (2026-09-10). Mock — band bilan baholanadi, foiz qo'llanmaydi.
    _pass = None
    if o.kind != "mock":
        _r = (db.query(models.ExamPassRule)
              .filter(models.ExamPassRule.kind == o.kind).first())
        _pass = _r.percent if _r else roles.DEFAULT_EXAM_PASS.get(o.kind)

    ex = models.Exam(
        group_id=o.group_id, kind=o.kind, unit_no=o.unit_no,
        title=roles.exam_title(o.kind, o.unit_no),
        date=o.date, status="approved", pass_percent=_pass,
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
    if not _in_user_branches(db, user, o.branch_id):
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

