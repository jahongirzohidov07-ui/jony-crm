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
    # Qarzdorligicha guruhdan chiqarilgan o'quvchi belgisi
    ("0006_archive_when_paid", [
        "ALTER TABLE students ADD COLUMN archive_when_paid INTEGER",
    ]),
    # HR dan ochilgan ustoz/support hisoblari Ustozlar bo'limida ham
    # ko'rinishi uchun: avval ism mos egasiz kartaga bog'laymiz,
    # qolganlarga yangi karta ochamiz.
    ("0007_teacher_cards_for_users", [
        "UPDATE teachers SET user_id = ("
        " SELECT u.id FROM users u WHERE u.full_name = teachers.full_name"
        " AND u.role IN ('teacher','support_teacher')"
        " AND NOT EXISTS (SELECT 1 FROM teachers t2"
        "                 WHERE t2.user_id = u.id) LIMIT 1)"
        " WHERE teachers.user_id IS NULL AND EXISTS ("
        " SELECT 1 FROM users u WHERE u.full_name = teachers.full_name"
        " AND u.role IN ('teacher','support_teacher')"
        " AND NOT EXISTS (SELECT 1 FROM teachers t2"
        "                 WHERE t2.user_id = u.id))",
        "INSERT INTO teachers (full_name, user_id, branch_id, is_active)"
        " SELECT u.full_name, u.id, u.branch_id, 1 FROM users u"
        " WHERE u.role IN ('teacher','support_teacher')"
        " AND u.is_active = 1"
        " AND NOT EXISTS (SELECT 1 FROM teachers t"
        "                 WHERE t.user_id = u.id)",
    ]),
    # Ota-ona havolasiga muddat qo'shildi (roles.PARENT_TOKEN_VALIDITY_DAYS).
    # Faqat ustun qo'shiladi - mavjud tokenlarning muddati bu yerda
    # BELGILANMAYDI (SQLite/Postgres orasida sana arifmetikasi
    # boshqacha yoziladi, xato qilib xavfli DB-maxsus SQL yozgandan
    # ko'ra ilova kodida bajarish xavfsizroq). NULL qolgan eskilar
    # birinchi "Ota-ona havolasi" so'ralganda students.py:parent_link()
    # orqali backfill qilinadi - hech kim hozircha yo'qotmaydi.
    ("0008_students_parent_token_expiry", [
        "ALTER TABLE students ADD COLUMN parent_token_expires_at TIMESTAMP",
    ]),
    # Ko'nikma (skill) kesimidagi daraja uchun: mavjud mashq
    # natijalariga "qaysi ko'nikma" ustuni. Eski yozuvlar NULL bo'lib
    # qoladi va UMUMIY darajaga hisoblanaveradi (hech kim ball
    # yo'qotmaydi), faqat ko'nikma kesimida ko'rinmaydi.
    ("0009_exercise_skill", [
        "ALTER TABLE exercise_results ADD COLUMN skill VARCHAR",
        # 2026-08-12: yashirin (individual) chegirma
        "ALTER TABLE discounts ADD COLUMN hidden INTEGER",
    ]),
    # 2026-08-27: kontent-plan Excel jadvalidagi ustunlar va
    # postlar natijasini LINK orqali avtomat yig'ish belgilari.
    ("0010_content_plan", [
        "ALTER TABLE contents ADD COLUMN proof TEXT",
        "ALTER TABLE contents ADD COLUMN shoot_date DATE",
        "ALTER TABLE contents ADD COLUMN kpi_target VARCHAR",
        "ALTER TABLE contents ADD COLUMN conclusion TEXT",
        "ALTER TABLE contents ADD COLUMN series VARCHAR",
        "ALTER TABLE content_metrics ADD COLUMN source VARCHAR",
        "ALTER TABLE content_metrics ADD COLUMN fetched_at TIMESTAMP",
        "ALTER TABLE content_metrics ADD COLUMN fetch_note VARCHAR",
    ]),
    # 2026-08-28, Jahongir: "o'quvchiga maxsus link beriladi ... u
    # o'quvchi ro'yxatdan o'tadi va adminlarga so'rov boradi yangi lid
    # bo'lib". Referal uchun uchta bog'lanish kerak.
    ("0011_referral", [
        "ALTER TABLE students ADD COLUMN ref_code VARCHAR",
        "ALTER TABLE students ADD COLUMN referred_by_student_id INTEGER",
        "ALTER TABLE leads ADD COLUMN referrer_student_id INTEGER",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_students_ref_code "
        "ON students (ref_code)",
        "CREATE INDEX IF NOT EXISTS ix_students_referred_by "
        "ON students (referred_by_student_id)",
        "CREATE INDEX IF NOT EXISTS ix_leads_referrer "
        "ON leads (referrer_student_id)",
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
