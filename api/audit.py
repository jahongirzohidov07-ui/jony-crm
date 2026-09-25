"""Audit log - kim nimani o'zgartirgani.

Asosiy g'oya: yozuvni faqat QO'SHISH mumkin. Hech kim, hatto asoschi
ham, audit yozuvini o'chira yoki tahrirlay olmaydi. Shuning uchun
"kim chegirma berdi", "kim qarzni o'chirdi" degan savolga har doim
javob bo'ladi.
"""
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

import models

# Kuzatilmaydigan texnik maydonlar - ular shovqin qo'shadi.
IGNORED_FIELDS = {"updated_at", "created_at", "id", "public_id"}

# Amal turlari va ularning o'zbekcha nomi.
ACTIONS = {
    "create": "Yaratildi",
    "update": "O'zgartirildi",
    "delete": "O'chirildi",
    "discount": "Chegirma berildi",
    "debt_write_off": "Qarzdorlik o'chirildi",
    "payment_cancel": "To'lov bekor qilindi",
    "group_remove": "Guruhdan chiqarildi",
    "group_move": "Boshqa guruhga o'tkazildi",
    "activate": "Faollashtirildi",
    "phone_change": "Telefon o'zgartirildi",
    "login": "Tizimga kirdi",
    "role_change": "Roli o'zgartirildi",
    "salary_change": "Oyligi o'zgartirildi",
    "approve": "Tasdiqlandi",
    "reject": "Rad etildi",
    "cancel": "Bekor qilindi",
    "att_mark": "Yo'qlama belgilandi",
    "att_remove": "Yo'qlama olib tashlandi",
    # 2026-09-16
    "merge": "Birlashtirildi",
    "import": "Import qilindi",
    # 2026-09-25: baraban (lid testi oxiridagi sovg'a)
    "wheel_spin": "Baraban aylantirildi",
    "wheel_coins": "Baraban tangasi berildi",
    "wheel_prizes": "Baraban sozlamasi o'zgardi",
}

# Kuzatiladigan obyektlar.
ENTITIES = {
    "student": "O'quvchi",
    "parent": "Ota-ona",
    "user": "Xodim",
    "teacher": "O'qituvchi",
    "lead": "Lid",
    "group": "Guruh",
    "payment": "To'lov",
    "contract": "Shartnoma",
    "expense": "Xarajat",
    "branch": "Filial",
    "complaint": "Shikoyat",
    "reward": "Sovg'a",
    "exam": "Imtihon",
    "exam_template": "Test bazasi",
    "discount": "Chegirma",
    "task": "Vazifa",
    "asset": "Aktiv",
    # 2026-08-21, Jahongir: "yoqlamada yoq qoyganimda qandaydur bor
    # bolib qolibdi... audit bolimida kimga qanday yoqlama qoygani
    # korinadimi" — endi yo'qlama ham auditda.
    "attendance": "Yo'qlama",
    # 2026-09-16: HR bo'limlari
    "candidate": "Nomzod",
    "conduct": "Na'munali xodim",
    "hr_blacklist": "Qora ro'yxat",
    "support_adjustment": "Support jarimasi",
    "examiner_adjustment": "Examiner jarimasi",
    # 2026-09-25: baraban sozlamasi
    "settings": "Sozlamalar",
}


def _fmt(v: Any) -> Optional[str]:
    """Qiymatni o'qiladigan matnga aylantiradi."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "ha" if v else "yo'q"
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def log(
    db: Session,
    user,
    *,
    entity: str,
    action: str,
    entity_id: Optional[int] = None,
    entity_label: Optional[str] = None,
    field: Optional[str] = None,
    old_value: Any = None,
    new_value: Any = None,
    note: Optional[str] = None,
    branch_id: Optional[int] = None,
    commit: bool = False,
) -> models.AuditLog:
    """Bitta audit yozuvi qo'shadi. commit=False - chaqiruvchi o'zi
    commit qiladi (bir tranzaksiyada bir nechta yozuv bo'lishi mumkin)."""
    row = models.AuditLog(
        user_id=getattr(user, "id", None),
        username=getattr(user, "username", None),
        user_name=getattr(user, "full_name", None),
        user_role=getattr(user, "role", None),
        entity=entity,
        entity_id=entity_id,
        entity_label=entity_label,
        action=action,
        field=field,
        old_value=_fmt(old_value),
        new_value=_fmt(new_value),
        note=note,
        branch_id=branch_id,
    )
    db.add(row)
    if commit:
        db.commit()
    return row


def log_changes(
    db: Session,
    user,
    *,
    entity: str,
    obj,
    changes: dict,
    label_attr: str = "full_name",
    note: Optional[str] = None,
) -> int:
    """Obyektga qo'llanilayotgan o'zgarishlarni maydon-maydon yozadi.

    DIQQAT: bu funksiya o'zgarishlar QO'LLANISHIDAN OLDIN chaqirilishi
    kerak - aks holda eski qiymat allaqachon yo'qolgan bo'ladi.

    Faqat HAQIQATDA o'zgargan maydonlar yoziladi: forma butun obyektni
    yuborganda o'zgarmagan maydonlar shovqin qo'shmasin.
    """
    label = getattr(obj, label_attr, None)
    branch_id = getattr(obj, "branch_id", None)
    n = 0
    for field, new in changes.items():
        if field in IGNORED_FIELDS:
            continue
        old = getattr(obj, field, None)
        if _fmt(old) == _fmt(new):
            continue
        action = "update"
        if field in ("phone", "parent_phone", "phone2"):
            action = "phone_change"
        elif field == "role":
            action = "role_change"
        elif field == "fix_salary":
            action = "salary_change"
        log(db, user, entity=entity, action=action,
            entity_id=getattr(obj, "id", None), entity_label=label,
            field=field, old_value=old, new_value=new, note=note,
            branch_id=branch_id)
        n += 1
    return n
