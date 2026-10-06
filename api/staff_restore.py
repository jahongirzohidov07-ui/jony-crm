"""KETGAN XODIMNI QAYTARISH — HR uchun (2026-10-06).

Jahongir: "arxivdagi ketgan xodimlarni akkauntlarini tiklash
qaytarishni ham qo'shib ber hrga".

Ilgari xodimni qaytarish faqat Arxiv sahifasida, oddiy "faol" belgisi
bilan bo'lardi — HR'ning "Ketganlar arxivi"da tugma yo'q edi, parol
esdan chiqqan bo'lsa kira olmasdi, "qizil yo'lak" (qayta olinmaydi)
belgilangan odam ham indamay qaytib ketardi.

QOIDALAR (xodim hisobini tahrirlash bilan bir xil himoyalar):
  - asoschi va filial rahbari hisobini faqat asoschi qaytaradi;
  - filial rahbari faqat o'z filialidagini;
  - qora ro'yxatdagi odam qaytarilmaydi (blacklist.guard_hire);
  - "qizil yo'lak" — avval ogohlantirish (409), tasdiq bilan qaytadi;
  - ixtiyoriy: parol standartga (jonyjony) qaytariladi — kirganda
    tizim yangi parol qo'yishni majburiy so'raydi.
Ketish sababi va suhbat yozuvi O'CHIRILMAYDI — audit va chiqish
suhbati (staff_exits) tarixda qoladi; faqat foydalanuvchi kartasidagi
"ketgan" belgisi tozalanadi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import hash_password, is_partner_head, require_role
from common import _in_user_branches
from database import get_db

router = APIRouter()


class RestoreIn(BaseModel):
    reset_password: bool = False
    force: bool = False
    note: Optional[str] = None


def _guard(db: Session, user, target) -> None:
    if target.role in tuple(roles.EXTERNAL_ROLES):
        raise HTTPException(400, "Bu xodim hisobi emas")
    if target.role in (roles.FOUNDER, roles.BRANCH_MANAGER) \
            and user.role != roles.FOUNDER and not is_partner_head(user):
        raise HTTPException(403, "Asoschi va filial rahbari hisobini faqat "
                                 "asoschi qaytaradi")
    if user.role == roles.BRANCH_MANAGER and not is_partner_head(user) \
            and not _in_user_branches(db, user, target.branch_id):
        raise HTTPException(403, "Faqat o'z filialingiz xodimini "
                                 "qaytara olasiz")


@router.post("/api/staff/{user_id}/restore")
def restore_staff(user_id: int, payload: RestoreIn,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.HR_ACCESS))):
    t = db.query(models.User).get(user_id)
    if not t:
        raise HTTPException(404, "Xodim topilmadi")
    if t.is_active:
        raise HTTPException(400, "Xodim allaqachon faol")
    _guard(db, user, t)
    import blacklist as _bl
    _bl.guard_hire(db, t.full_name, t.phone)
    if t.exit_type == "red" and not payload.force:
        raise HTTPException(409, detail={
            "message": (f"{t.full_name} \"Qizil yo'lak\"da — qayta ishga "
                        "olinmaydi deb belgilangan"
                        + (f" ({t.exit_reason})" if t.exit_reason else "")
                        + ". Baribir qaytarasizmi?"),
            "can_force": True,
        })
    old_exit = (t.exit_type, t.exit_date, t.exit_reason)
    t.is_active = 1
    t.exit_type = None
    t.exit_date = None
    t.exit_reason = None
    # Ustoz/support kartasi ham qaytadi (bo'shatishdagi sinxronning
    # teskarisi — aks holda akkaunt faol, karta yopiq qolardi)
    tc = (db.query(models.Teacher)
          .filter(models.Teacher.user_id == t.id).first())
    if tc is not None and not tc.is_active:
        tc.is_active = 1
        tc.left_date = None
    if payload.reset_password:
        t.password_hash = hash_password(roles.DEFAULT_PASSWORD)
    note = (payload.note or "").strip()
    audit.log(db, user, entity="user", action="restore", entity_id=t.id,
              entity_label=t.full_name, field="is_active",
              old_value=(f"ketgan {old_exit[1] or ''} {old_exit[0] or ''}"
                         .strip()),
              new_value="faol",
              note="; ".join(filter(None, [
                  note or None,
                  "parol standartga qaytarildi" if payload.reset_password
                  else None,
                  "qizil yo'lakdan qaytarildi" if old_exit[0] == "red"
                  else None])) or None,
              branch_id=t.branch_id)
    db.commit()
    return {"ok": True, "id": t.id, "full_name": t.full_name,
            "login": t.username,
            "password_reset": bool(payload.reset_password)}


@router.post("/api/staff/teacher-card/{teacher_id}/restore")
def restore_teacher_card(teacher_id: int, db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.HR_ACCESS))):
    """Akkauntsiz ustoz kartasi (eski yozuv) — faqat karta qaytadi."""
    tc = db.query(models.Teacher).get(teacher_id)
    if not tc:
        raise HTTPException(404, "Ustoz kartasi topilmadi")
    if tc.is_active:
        raise HTTPException(400, "Karta allaqachon faol")
    if user.role == roles.BRANCH_MANAGER and not is_partner_head(user) \
            and not _in_user_branches(db, user, tc.branch_id):
        raise HTTPException(403, "Faqat o'z filialingiz ustozini "
                                 "qaytara olasiz")
    import blacklist as _bl
    _bl.guard_hire(db, tc.full_name, getattr(tc, "phone", None))
    tc.is_active = 1
    tc.left_date = None
    audit.log(db, user, entity="teacher", action="restore", entity_id=tc.id,
              entity_label=tc.full_name, field="is_active",
              new_value="faol", branch_id=tc.branch_id)
    db.commit()
    return {"ok": True, "id": tc.id, "full_name": tc.full_name}
