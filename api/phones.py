"""TELEFON RAQAMLARI — BITTA FORMAT (2026-09-16).

Jahongir tanlagan taklif (#30): "telefon raqamlarini bitta formatga
keltirish". Qoida roles.normalize_phone da: O'zbekiston raqami bazada
9 raqam ("901234567") bo'lib turadi, sayt uni "+998 90 123 45 67"
qilib ko'rsatadi (PhoneInput / formatPhone).

Bu modul ikki ishni qiladi:
  1. YOZISHDA — model darajasida (SQLAlchemy hodisasi): qaysi forma,
     import yoki onlayn ariza bo'lishidan qat'i nazar, bazaga faqat
     bir xil ko'rinish tushadi. Yangi endpoint yozilsa ham unutilmaydi.
  2. ESKI YOZUVLAR — bir martalik tozalash, vaqt chegarasi bilan va
     davomli: har jadval-ustun tugagach belgi qo'yiladi, keyingi
     ishga tushishda qolganidan davom etadi.

DIQQAT: loginlarga (users.username) TEGILMAYDI — kirish buzilmaydi.
Login baribir 9 va 12 xonali ko'rinishda qabul qilinadi (auth_users)."""
import time

from sqlalchemy import event, text

import models
import roles

PHONE_FIELDS = [
    (models.User, ("phone",)),
    (models.Teacher, ("phone",)),
    (models.Student, ("phone", "parent_phone")),
    (models.Lead, ("phone",)),
    (models.DeletedLead, ("phone",)),
    (models.Candidate, ("phone",)),
    (models.Parent, ("phone", "phone2")),
    (models.HrBlacklist, ("phone",)),
]

BACKFILL_KEY = "phone_norm_v1"


def _normalize_target(mapper, connection, target):
    for attr in _FIELDS_BY_CLASS.get(type(target), ()):
        val = getattr(target, attr, None)
        if val is None:
            continue
        new = roles.normalize_phone(val)
        if new != val:
            setattr(target, attr, new)


_FIELDS_BY_CLASS = {cls: cols for cls, cols in PHONE_FIELDS}
for _cls, _cols in PHONE_FIELDS:
    if not event.contains(_cls, "before_insert", _normalize_target):
        event.listen(_cls, "before_insert", _normalize_target)
        event.listen(_cls, "before_update", _normalize_target)


def normalize_existing(db, budget_s: float = 8.0) -> dict:
    """Eski yozuvlarni bir martalik tozalaydi. Qaytaradi:
    {"done": bool, "changed": {jadval.ustun: soni}}."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, BACKFILL_KEY):
        return {"done": True, "changed": {}}
    started = time.monotonic()
    changed = {}
    for cls, cols in PHONE_FIELDS:
        table = cls.__tablename__
        for col in cols:
            key = f"{BACKFILL_KEY}:{table}.{col}"
            if _seed_done(db, key):
                continue
            if time.monotonic() - started > budget_s:
                return {"done": False, "changed": changed}
            try:
                rows = db.execute(text(
                    f"SELECT id, {col} FROM {table} "
                    f"WHERE {col} IS NOT NULL")).fetchall()
                upd = []
                for rid, val in rows:
                    new = roles.normalize_phone(val)
                    if new != val:
                        upd.append({"i": rid, "v": new})
                if upd:
                    db.execute(text(
                        f"UPDATE {table} SET {col} = :v WHERE id = :i"), upd)
                db.commit()
                changed[f"{table}.{col}"] = len(upd)
                _seed_mark(db, key)
            except Exception as exc:
                db.rollback()
                try:
                    db.add(models.ErrorLog(
                        path=f"phone_norm.{table}.{col}", method="internal",
                        detail=f"{type(exc).__name__}: {exc}"[:4000]))
                    db.commit()
                except Exception:
                    db.rollback()
                return {"done": False, "changed": changed}
    _seed_mark(db, BACKFILL_KEY)
    if any(changed.values()):
        print("[phones] formatlandi: " + ", ".join(
            f"{k}={v}" for k, v in changed.items() if v))
    return {"done": True, "changed": changed}
