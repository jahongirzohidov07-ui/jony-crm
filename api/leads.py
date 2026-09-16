"""Auto-extracted from main.py during refactor (split-main). Domain: leads."""
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

def _get_lead_in_scope(db: Session, lead_id: int, user: models.User) -> models.Lead:
    lead = db.query(models.Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lid topilmadi")
    if not _in_user_branches(db, user, lead.branch_id):
        raise HTTPException(403, "Bu lid boshqa filialga tegishli")
    return lead

def _validate_lead_fields(source: Optional[str], stage: Optional[str]):
    if source is not None and source not in roles.LEAD_SOURCES:
        raise HTTPException(400, "Noto'g'ri manba")
    if stage is not None and stage not in roles.LEAD_STAGES:
        raise HTTPException(400, "Noto'g'ri bosqich")

# =====================================================================
#  SAYT (jonyacademy.uz) UCHUN OCHIQ ARIZA
#
#  2026-08-13, Jahongir: "saytimizga ariza qoldirsa avtomat JonyOS ga
#  qaysi filial tanlangan bo'lsa shu filialga lid bolib tushsin va
#  manbasi website bo'ladigan qil".
#
#  Auth YO'Q - sayt tashqarida turadi. Shuning uchun himoya:
#  honeypot maydon, telefon tekshiruvi, bir xil raqamdan 24 soatda
#  bitta ariza va IP bo'yicha soatiga cheklov.
# =====================================================================

_WEB_LEAD_HITS: dict = {}
_WEB_LEAD_MAX_PER_HOUR = 30


def _web_rate_ok(ip: str) -> bool:
    now = datetime.utcnow()
    hits = [t for t in _WEB_LEAD_HITS.get(ip, []) if (now - t).seconds < 3600]
    hits.append(now)
    _WEB_LEAD_HITS[ip] = hits[-100:]
    return len(hits) <= _WEB_LEAD_MAX_PER_HOUR


@router.get("/api/public/branches")
def public_branches(db: Session = Depends(get_db)):
    """Sayt formasidagi filial ro'yxati. Auth yo'q - faqat nom va id."""
    rows = db.query(models.Branch).order_by(models.Branch.name).all()
    return [{"id": b.id, "name": b.name} for b in rows
            if not (b.name or "").lower().startswith("test")]


@router.post("/api/public/lead")
def public_lead(payload: dict, request: Request,
                db: Session = Depends(get_db)):
    """Saytdagi "Ariza qoldirish" formasi. Auth YO'Q.

    Kutiladigan maydonlar:
      full_name (majburiy), phone (majburiy), branch_id yoki branch,
      course, note, page, utm_source, hp (honeypot - bo'sh bo'lishi kerak)
    """
    ip = (request.client.host if request.client else "?") or "?"
    if not _web_rate_ok(ip):
        raise HTTPException(429, "Juda ko'p so'rov — birozdan keyin urinib "
                                 "ko'ring")

    def _s(key, limit=200):
        return str(payload.get(key) or "").strip()[:limit]

    # Honeypot: odam ko'rmaydigan maydon. Bot to'ldiradi - jimgina
    # "ok" qaytaramiz, lekin bazaga yozmaymiz.
    if _s("hp", 50):
        return {"ok": True}

    full_name = " ".join(_s("full_name", 120).split())
    phone = _s("phone", 40)
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(full_name) < 3:
        raise HTTPException(400, "Ismingizni to'liq yozing")
    if len(digits) < 7:
        raise HTTPException(400, "Telefon raqamini to'g'ri kiriting")

    branch = None
    if payload.get("branch_id"):
        try:
            branch = db.query(models.Branch).get(int(payload["branch_id"]))
        except (TypeError, ValueError):
            branch = None
    if branch is None and _s("branch", 80):
        # Saytda filial "Bekobod shahar" deb yozilgan bo'lishi mumkin,
        # bizda esa "Bekobod 1". Shuning uchun aniq moslik topilmasa,
        # birinchi so'z bo'yicha qidiramiz (Jahongir, 2026-08-13:
        # saytdagi mavjud forma ulanmoqda).
        nm = _s("branch", 80).lower().strip()
        all_b = db.query(models.Branch).order_by(models.Branch.id).all()
        branch = next((b for b in all_b if (b.name or "").lower() == nm),
                      None)
        if branch is None:
            head = nm.split()[0] if nm else ""
            if head:
                branch = next(
                    (b for b in all_b
                     if (b.name or "").lower().startswith(head)
                     or head in (b.name or "").lower()), None)

    # TAKROR: shu raqamdan 24 soat ichida ariza kelgan bo'lsa, yangi
    # lid ochilmaydi - odam tugmani ikki marta bosgan bo'lishi mumkin.
    tail = digits[-9:]
    since = datetime.utcnow() - timedelta(hours=24)
    for l in (db.query(models.Lead)
              .filter(models.Lead.created_at >= since).all()):
        d = "".join(ch for ch in (l.phone or "") if ch.isdigit())
        if d and d[-9:] == tail:
            return {"ok": True, "duplicate": True, "lead_id": l.id}

    course = _s("course", 120)
    page = _s("page", 200)
    utm = _s("utm_source", 80)
    extra = _s("note", 500)
    note_lines = ["Sayt orqali ariza (jonyacademy.uz)"]
    if course:
        note_lines.append(f"Yo'nalish: {course}")
    if branch:
        note_lines.append(f"Tanlagan filiali: {branch.name}")
    if extra:
        note_lines.append(f"Izoh: {extra}")
    if page:
        note_lines.append(f"Sahifa: {page}")
    if utm:
        note_lines.append(f"UTM: {utm}")

    lead = models.Lead(
        full_name=full_name,
        phone=phone,
        source="website",
        stage=roles.LEAD_SOURCE_DEFAULT_STAGE.get("website", "new"),
        branch_id=branch.id if branch else None,
        note="\n".join(note_lines),
        created_by="Sayt")
    db.add(lead); db.commit(); db.refresh(lead)
    _ensure_public_id(db, "lead", lead)
    db.commit()

    # Ariza javobsiz qolmasin: filial administratoriga vazifa.
    try:
        _hr_task(db,
                 title=f"Saytdan ariza: {full_name} ({lead.public_id or lead.id})",
                 body=("\n".join(note_lines)
                       + f"\nTelefon: {phone}\n"
                         "Iltimos, bugunning o'zida qo'ng'iroq qiling."),
                 to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER,
                           roles.SALES_HEAD, roles.BRANCH_MANAGER],
                 branch_id=lead.branch_id, days=1, priority="high")
        db.commit()
    except Exception:
        db.rollback()

    return {"ok": True, "lead_id": lead.id,
            "public_id": lead.public_id,
            "branch": branch.name if branch else None}


@router.get("/api/leads", response_model=List[schemas.LeadOut])
def list_leads(
    stage: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    backfill_missing_ids(db, "lead", models.Lead)
    q = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id)
    if stage:
        q = q.filter(models.Lead.stage == stage)
    else:
        # O'quvchiga aylangan lid doskada turmaydi - u endi Talabalar
        # bo'limida. Voronka hisobotlari to'g'ridan-to'g'ri bazadan
        # o'qiydi, shuning uchun statistika buzilmaydi.
        q = q.filter(models.Lead.stage != "converted")
    return q.order_by(models.Lead.updated_at.desc(), models.Lead.id.desc()).all()

@router.post("/api/leads", response_model=schemas.LeadOut)
def create_lead(
    payload: schemas.LeadCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    if not payload.full_name.strip():
        raise HTTPException(400, "Ism-familiyani kiriting")
    _validate_lead_fields(payload.source, payload.stage)

    # DUBLIKAT: shu telefon bilan lid yoki o'quvchi allaqachon bormi?
    # Bitta odam ikki marta yozilib ketmasin. "force" bilan baribir
    # qo'shish mumkin (masalan, aka-uka bitta raqamdan yozilsa).
    digits = "".join(ch for ch in (payload.phone or "") if ch.isdigit())
    if digits and len(digits) >= 7 and not payload.force:
        tail = digits[-9:]
        dup_lead = None
        for l in db.query(models.Lead).filter(
                models.Lead.phone.isnot(None),
                models.Lead.stage.notin_(("rejected",))).all():
            d = "".join(ch for ch in (l.phone or "") if ch.isdigit())
            if d and d[-9:] == tail:
                dup_lead = l
                break
        dup_student = None
        # ARXIVDAGILAR ham tekshiriladi (Jahongir, 2026-08-13: "agar
        # nomer togri kelib qolsa ... arxiv bilan yoki o'qiyotgan bor
        # o'quvchi bilan bunday o'quvchi bor deb tavsiya qilsin") —
        # ketgan o'quvchi qaytib kelayotgan bo'lishi mumkin, uni yangi
        # lid qilib emas, arxivdan tiklash kerak.
        if not dup_lead:
            for s in db.query(models.Student).all():
                for ph in (s.phone, s.parent_phone):
                    d = "".join(ch for ch in (ph or "") if ch.isdigit())
                    if d and d[-9:] == tail:
                        dup_student = s
                        break
                if dup_student:
                    break
        if dup_lead or dup_student:
            who = dup_lead.full_name if dup_lead else dup_student.full_name
            kind = "lid" if dup_lead else "o'quvchi"
            extra = ""
            if dup_student is not None and dup_student.status in (
                    "archived", "left"):
                kind = "ARXIVDAGI o'quvchi"
                extra = (" U ilgari o'qigan — yangi lid ochish o'rniga "
                         "Arxiv bo'limidan tiklasangiz, to'lov va davomat "
                         "tarixi saqlanib qoladi.")
            elif dup_student is not None:
                extra = (f" U hozir {'guruhda o‘qiyapti' if dup_student.group_id else 'bazada bor'}"
                         f" ({dup_student.status}).")
            raise HTTPException(
                409, f"Bu telefon raqami bilan {kind} allaqachon bor: "
                     f"{who}.{extra} Bir oila vakilimi (aka-uka / "
                     "opa-singil) yoki raqamni adashib kiritdingizmi? "
                     "Bir oiladan bo'lsa, tasdiqlang — bitta raqam bilan "
                     "yozilaveradi.")

    # DUBLIKAT (ism bo'yicha): bir xil ism-familiyali lid yoki talaba
    # bo'lsa — adashib qayta kiritishning oldini olamiz. Yangi odam
    # bo'lsa, tasdiqlab kiritaveradi (force).
    if not payload.force:
        nm = " ".join(payload.full_name.split()).lower()
        same_lead = next(
            (l for l in db.query(models.Lead)
             .filter(models.Lead.stage != "rejected").all()
             if " ".join((l.full_name or "").split()).lower() == nm), None)
        same_student = None
        if not same_lead:
            same_student = next(
                (st for st in db.query(models.Student).all()
                 if " ".join((st.full_name or "").split()).lower() == nm),
                None)
        if same_lead or same_student:
            kind = "lid" if same_lead else "o'quvchi"
            extra = ""
            if same_student is not None:
                if same_student.status in ("archived", "left"):
                    kind = "ARXIVDAGI o'quvchi"
                    extra = (" Uni Arxiv bo'limidan tiklash mumkin — "
                             "tarixi saqlanib qoladi.")
                else:
                    extra = f" (holati: {same_student.status})"
            raise HTTPException(
                409, f"Bunday ismli {kind} allaqachon bor: "
                     f"{(same_lead or same_student).full_name}.{extra} "
                     f"Adashib qayta kiritib qo'ymayapsizmi? Agar bu "
                     f"boshqa (yangi) odam bo'lsa, tasdiqlang.")

    # Bosqich berilmasa, manbaga qarab o'zi tanlanadi: tashrif bilan kelgan
    # odam "unga qo'ng'iroq qilish kerak" bosqichini o'tib bo'lgan.
    stage = payload.stage or roles.LEAD_SOURCE_DEFAULT_STAGE.get(payload.source, "new")

    lead = models.Lead(
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        source=payload.source,
        stage=stage,
        address=payload.address,
        school=payload.school,
        grade=payload.grade,
        note=payload.note,
        branch_id=payload.branch_id if payload.branch_id is not None else user.branch_id,
        assigned_user_id=payload.assigned_user_id,
        created_by=user.full_name,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
def update_lead(
    lead_id: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    lead = _get_lead_in_scope(db, lead_id, user)
    _validate_lead_fields(payload.source, payload.stage)

    data = payload.model_dump(exclude_unset=True)
    if data.get("stage") == "converted" and not lead.converted_student_id:
        raise HTTPException(
            400,
            "Lidni bu bosqichga qo'lda surib bo'lmaydi - "
            "\"O'quvchiga aylantirish\" tugmasidan foydalaning",
        )
    for k, v in data.items():
        setattr(lead, k, v)
    db.commit()
    db.refresh(lead)
    return lead

@router.get("/api/leads/delete-reasons")
def lead_delete_reasons(user=Depends(get_current_user)):
    """O'chirish sabablari ro'yxati — ekran shundan to'ldiriladi."""
    return {"rows": [{"key": k, "label": lbl, "real_loss": real}
                     for k, lbl, real in roles.LEAD_DELETE_REASONS]}


@router.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    reason: str = None,
    note: str = None,
    db: Session = Depends(get_db),
    # 2026-09-16, Jahongir: "lidlarni ochiradigan qilib ber lid ochirib
    # bolmayabdi" — ilgari faqat asoschi/filial rahbari o'chira olardi,
    # administrator 403 olardi. Endi lid bilan ishlaydigan hamma (o'z
    # filialidagini, sabab bilan).
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidni o'chirish — SABAB BILAN va ARXIVGA (2026-08-30).

    Jahongir: "lidni o'chirishni ham sabablar qo'shib qo'y, ichida
    ADASHIB KIRITILIB YUBORILIBDI bo'lsin".

    Ilgari lid butunlay o'chib ketardi: na yozuvi, na sababi
    qolardi. Endi yozuv leads_deleted ga ko'chiriladi — kim, qachon,
    nima sababdan. Voronka va hisobotlar leads jadvalidan chiqadi,
    shuning uchun ular bir zarra o'zgarmaydi.

    SABAB MAJBURIY: "adashib kiritilgan" bilan "qiziqmadi" ni
    ajratmasak, statistika yolg'on gapiradi — birinchisi umuman lid
    emas edi, ikkinchisi haqiqiy yo'qotish."""
    lead = _get_lead_in_scope(db, lead_id, user)
    code = (reason or "").strip()
    if code not in roles.LEAD_DELETE_LABELS:
        raise HTTPException(
            400, "O'chirish sababini ro'yxatdan tanlang — statistika "
                 "shu asosda yig'iladi")

    db.add(models.DeletedLead(
        lead_id=lead.id, public_id=lead.public_id,
        full_name=lead.full_name, phone=lead.phone,
        source=lead.source, stage=lead.stage,
        branch_id=lead.branch_id,
        assigned_user_id=lead.assigned_user_id,
        note=lead.note, created_by=lead.created_by,
        created_at=lead.created_at,
        reason=code, reason_note=(note or "").strip() or None,
        deleted_by=user.full_name))
    audit.log(db, user, entity="lead", action="delete",
              entity_id=lead.id, entity_label=lead.full_name,
              branch_id=lead.branch_id,
              old_value=f"{lead.full_name} ({lead.phone or '—'})",
              new_value=roles.LEAD_DELETE_LABELS[code],
              note=(note or None))
    db.delete(lead)
    db.commit()
    return {"ok": True, "reason": roles.LEAD_DELETE_LABELS[code]}


@router.get("/api/leads/deleted")
def deleted_leads(limit: int = 200, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.LEAD_ACCESS))):
    """O'chirilgan lidlar arxivi — hech narsa yo'qolmagani ko'rinsin."""
    q = db.query(models.DeletedLead).filter(
        models.DeletedLead.restored_at.is_(None))
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.DeletedLead.branch_id == user.branch_id)
    rows = q.order_by(models.DeletedLead.id.desc()).limit(
        max(1, min(int(limit), 500))).all()
    return {"rows": [{
        "id": r.id, "lead_id": r.lead_id, "public_id": r.public_id,
        "full_name": r.full_name, "phone": r.phone,
        "source": roles.LEAD_SOURCE_LABELS.get(r.source, r.source),
        "stage": r.stage,
        "reason": r.reason,
        "reason_label": roles.LEAD_DELETE_LABELS.get(r.reason, r.reason),
        "real_loss": r.reason in roles.LEAD_DELETE_REAL,
        "reason_note": r.reason_note,
        "deleted_by": r.deleted_by,
        "deleted_at": r.deleted_at.isoformat() if r.deleted_at else None,
    } for r in rows]}


@router.post("/api/leads/deleted/{row_id}/restore")
def restore_lead(row_id: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FULL_ACCESS))):
    """Xato o'chirilgan lidni qaytarish. Bir bosishda."""
    r = db.query(models.DeletedLead).get(row_id)
    if r is None or r.restored_at is not None:
        raise HTTPException(404, "Yozuv topilmadi yoki allaqachon qaytarilgan")
    lead = models.Lead(
        full_name=r.full_name, phone=r.phone,
        source=r.source or "other", stage=r.stage or "new",
        branch_id=r.branch_id, assigned_user_id=r.assigned_user_id,
        note=r.note, created_by=r.created_by,
        created_at=r.created_at)
    db.add(lead); db.commit(); db.refresh(lead)
    _ensure_public_id(db, "lead", lead)
    r.restored_at = datetime.utcnow()
    r.restored_by = user.full_name
    audit.log(db, user, entity="lead", action="restore",
              entity_id=lead.id, entity_label=lead.full_name,
              branch_id=lead.branch_id,
              new_value="arxivdan qaytarildi")
    db.commit()
    return {"ok": True, "lead_id": lead.id}

@router.post("/api/leads/{lead_id}/convert", response_model=schemas.StudentOut)
def convert_lead(
    lead_id: int,
    payload: schemas.LeadConvertRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidni haqiqiy o'quvchiga aylantiradi. Lid o'chirilmaydi - bosqichi
    "converted" bo'ladi va yaratilgan o'quvchiga bog'lanadi, shunda
    voronka statistikasi saqlanib qoladi."""
    lead = _get_lead_in_scope(db, lead_id, user)
    if lead.converted_student_id:
        raise HTTPException(400, "Bu lid allaqachon o'quvchiga aylantirilgan")

    # DUBLIKAT TEKSHIRUVI (2026-08-18).
    #
    # Jahongir: "shu boymirzayev Bekzod degan o'quvchi yoqolib qolib bir
    # paydo bolib qolyabdi, keyi yana men qoshib qoydim deyabdi admin".
    #
    # Tekshirganda ma'lum bo'ldiki, o'sha karta QO'LDA emas, aynan SHU
    # yo'l bilan — lid o'quvchiga aylantirilganda ochilgan. Va bu yo'lda
    # hech qanday tekshiruv yo'q edi: bir xil telefonli odam bazada
    # bo'lsa ham ikkinchi karta jimgina ochilaverardi. Endi "O'quvchi
    # qo'shish" formasidagi bilan bir xil ogohlantirish beriladi.
    if not payload.force:
        def _tail(v):
            d = "".join(ch for ch in str(v or "") if ch.isdigit())
            return d[-9:] if len(d) >= 9 else ""

        ph = _tail(lead.phone)
        nm = " ".join((lead.full_name or "").split()).lower()
        dup = None
        for st in db.query(models.Student).all():
            if ph and (_tail(st.phone) == ph or _tail(st.parent_phone) == ph):
                dup = st
                break
            if nm and " ".join((st.full_name or "").split()).lower() == nm \
                    and st.status != "archived":
                dup = st
                break
        if dup:
            _lbl = {"active": "faol", "frozen": "MUZLATILGAN",
                    "archived": "ARXIVDA", "trial": "sinov darsida"}
            br = db.query(models.Branch).get(dup.branch_id) \
                if dup.branch_id else None
            joy = f", {br.name} filialida" if br else ""
            raise HTTPException(
                409,
                f"Bu odam bazada allaqachon bor: {dup.full_name} "
                f"(#{dup.id}, {_lbl.get(dup.status, dup.status or '')}"
                f"{joy}). Yangi karta ochish o'rniga o'shani ishlating — "
                "aks holda bitta bolaga ikkita karta bo'lib, pul va "
                "davomat ikkiga bo'linib ketadi. Boshqa odam bo'lsa "
                "(masalan aka-uka) — tasdiqlang.")

    # Lidda yig'ilgan qo'shimcha ma'lumot (manzil, maktab, sinf) yo'qolib
    # ketmasligi uchun uni o'quvchining izohiga ko'chiramiz.
    extra = []
    if lead.address:
        extra.append(f"Manzil: {lead.address}")
    if lead.school:
        extra.append(f"Maktab: {lead.school}")
    if lead.grade:
        extra.append(f"Sinf: {lead.grade}")
    if lead.note:
        extra.append(lead.note)
    student_note = " · ".join(extra) if extra else None

    student = models.Student(
        full_name=lead.full_name,
        phone=lead.phone,
        group_id=payload.group_id,
        branch_id=lead.branch_id,
        enrolled_date=payload.enrolled_date or date.today(),
        # SINOV DARSI (2026-09-16, Jahongir: "liddan o'quvchiga
        # o'tkizganda sinov darsi bo'lib tushsin"). Ilgari darrov "faol"
        # bo'lardi, lekin hech qanday oylik yechilmasdi. Endi sinovda
        # turadi: 3 ta darsga kelsa yoki to'lov qilsa AVTOMAT faollashadi
        # va faollashgan kundan oylik yechiladi (_maybe_auto_activate).
        status="trial",
        note=student_note,
        # Kartada ham ko'rinsin — faqat eslatmada qolib ketmasin
        address=lead.address,
        school=lead.school,
        school_grade=lead.grade,
        # REFERAL (2026-08-28): lid kimning havolasidan kelgan bo'lsa,
        # bog'lanish o'quvchi kartasiga KO'CHADI. Aks holda bola to'lov
        # qilganda "kim olib keldi" savoli javobsiz qolardi va
        # chegirma hech qachon berilmasdi.
        referred_by_student_id=getattr(lead, "referrer_student_id", None),
    )
    db.add(student)
    db.flush()

    lead.stage = "converted"
    lead.converted_student_id = student.id
    db.commit()
    db.refresh(student)

    # 2026-08-18: bu yo'l "O'quvchi qo'shish" formasidan ORQADA qolgan
    # edi — uchta narsa qilinmasdi. Endi bir xil:
    #
    #  1) AUDITGA YOZILADI. Avval bu yerda hech qanday iz qolmasdi.
    #     Aynan shuning uchun Bekzodning kartasi "qayerdan paydo
    #     bo'ldi" degan savolga javob topib bo'lmadi — jurnalda u
    #     haqda bitta ham qator yo'q edi.
    #  2) O'QUVCHIGA HISOB ochiladi (login = telefon). Aks holda bola
    #     ilovaga kira olmasdi.
    #  3) GURUH BOG'LANISHI yoziladi — ko'p guruhli tizim shu jadvalga
    #     tayanadi, u bo'lmasa guruh kartadan yo'qolib qolishi mumkin.
    try:
        _ensure_public_id(db, "student", student)
    except Exception:
        pass
    audit.log(db, user, entity="student", action="create",
              entity_id=student.id, entity_label=student.full_name,
              branch_id=student.branch_id, new_value=student.full_name,
              note=f"Lid #{lead.id} o'quvchiga aylantirildi")
    db.commit()
    try:
        _ensure_student_account(db, student)
    except Exception:
        db.rollback()
    if student.group_id:
        try:
            attach_group(db, student, student.group_id, user,
                         joined=student.enrolled_date)
            db.commit()
        except Exception:
            db.rollback()
    db.refresh(student)
    return to_student_out(db, student)

@router.get("/api/sales/panel")
def sales_panel(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)

    rooms = {r.id: r for r in db.query(models.Room).all()}
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()

    # --- To'ldirilishi kerak bo'lgan guruhlar ---
    fill_rows = []
    for g in groups:
        n = sum(1 for s in students
                if s.group_id == g.id and s.status in ("active", "trial"))
        cap = _group_capacity(g, rooms)
        if not cap:
            continue
        pct = round(n / cap * 100, 1)
        band, band_label = roles.fill_band(pct)
        if pct >= 85:
            continue          # to'la guruh - ishlash shart emas
        fill_rows.append({
            "group_id": g.id,
            "group": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "", None),
            "level_label": roles.LEVEL_LABELS.get(g.level or "", None),
            "days": [d for d in (g.lesson_days or "").split(",") if d],
            "time": g.lesson_time,
            "students": n,
            "capacity": cap,
            "free": cap - n,
            "fill": pct,
            "band": band,
            "band_label": band_label,
        })
    # Eng ko'p bo'sh joyi bor guruh tepada - eng ko'p pul shu yerda
    fill_rows.sort(key=lambda r: (-r["free"], r["fill"]))

    # --- Shu oy ketganlar ---
    left_rows = []
    for s in students:
        if s.left_date and m_start <= s.left_date <= m_end:
            left_rows.append({
                "student_id": s.id,
                "full_name": s.full_name,
                "group": s.group.name if s.group else None,
                "teacher": (s.group.teacher.full_name
                            if s.group and s.group.teacher else None),
                "left_date": s.left_date.isoformat(),
                "months": (round((s.left_date - s.enrolled_date).days / 30.4, 1)
                           if s.enrolled_date else None),
                "balance": round(student_balance(db, s.id), 2),
            })
    left_rows.sort(key=lambda r: r["left_date"], reverse=True)

    return {
        "month": today.isoformat()[:7],
        "fill": {
            "rows": fill_rows[:20],
            "count": len(fill_rows),
            "free_seats": sum(r["free"] for r in fill_rows),
            # Bo'sh joylar qancha pul turadi
            "lost_income": round(sum(
                r["free"] * next((g.monthly_fee or 0) for g in groups
                                 if g.id == r["group_id"])
                for r in fill_rows), 2),
        },
        "left": {
            "rows": left_rows,
            "count": len(left_rows),
        },
    }

