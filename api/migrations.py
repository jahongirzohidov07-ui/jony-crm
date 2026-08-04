"""Versiyalangan sxema migratsiyalari.

Eski usul (_ensure_new_columns dagi "ALTER ... except: pass") o'rnida
endi har bir o'zgarish nomlanadi, BIR MARTA qo'llanadi va
schema_migrations jadvaliga yozib qo'yiladi. Xato bersa indamay
yutilmaydi — error_logs ga tushadi.

Yangi ustun/jadval kerak bo'lsa MIGRATIONS ro'yxatiga yangi versiya
qo'shiladi; eski versiyalar hech qachon o'zgartirilmaydi.
"""
from sqlalchemy import text

import models


MIGRATIONS = [
    ("0001_students_telegram", [
        "ALTER TABLE students ADD COLUMN tg_code VARCHAR",
        "ALTER TABLE students ADD COLUMN telegram_chat_id VARCHAR",
    ]),
    ("0002_students_parent_token", [
        "ALTER TABLE students ADD COLUMN parent_token VARCHAR",
    ]),
    ("0003_updated_at", [
        "ALTER TABLE students ADD COLUMN updated_at TIMESTAMP",
        "ALTER TABLE payments ADD COLUMN updated_at TIMESTAMP",
    ]),
    ("0004_users_recovery", [
        "ALTER TABLE users ADD COLUMN recovery_hash VARCHAR",
    ]),
    # Yordamchi o'qituvchi — ustozlik darajasi zinasida emas. Xodim
    # sifatida ochilgan support teacher kartasiga adashib "junior"
    # yozilib qolgan bo'lsa, tozalaymiz.
    ("0005_support_teacher_gradeless", [
        "UPDATE teachers SET grade = NULL WHERE user_id IN "
        "(SELECT id FROM users WHERE role = 'support_teacher')",
    ]),
]


def run(db) -> list:
    """Qo'llanmagan migratsiyalarni tartib bilan bajaradi.
    Qaytaradi: [(versiya, xato_matni_yoki_None), ...]"""
    applied = {m.version for m in db.query(models.SchemaMigration).all()}
    results = []
    for version, statements in MIGRATIONS:
        if version in applied:
            continue
        err = None
        for stmt in statements:
            try:
                db.execute(text(stmt))
                db.commit()
            except Exception as e:  # ustun allaqachon bor bo'lishi mumkin
                db.rollback()
                msg = str(e).lower()
                if "duplicate" in msg or "already exists" in msg \
                        or "duplicate column" in msg:
                    continue
                err = f"{stmt}: {e}"
                break
        db.add(models.SchemaMigration(version=version))
        db.commit()
        results.append((version, err))
        if err:
            try:
                db.add(models.ErrorLog(
                    path="migration", method=version, detail=err))
                db.commit()
            except Exception:
                db.rollback()
    return results
