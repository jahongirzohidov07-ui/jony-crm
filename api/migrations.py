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
    # 2026-08-30, Jahongir: "muzlatish sabablari statistikasi ham
    # kerak" — sabab endi ro'yxatdan tanlanadi va shu ustunga
    # yoziladi (erkin izoh frozen_note da qoladi).
    ("0012_freeze_reason", [
        "ALTER TABLE students ADD COLUMN frozen_reason VARCHAR",
        "CREATE INDEX IF NOT EXISTS ix_students_frozen_reason "
        "ON students (frozen_reason)",
    ]),
    # 2026-08-30, Jahongir: "lidni o'chirishni ham sabablar qo'shib
    # qo'y". Lid endi o'chirilmaydi — leads_deleted jadvaliga
    # ko'chiriladi (DeletedPayment bilan bir xil yo'l).
    #
    # DIQQAT — SHTAMP. Jadvalning O'ZINI create_all yaratadi, lekin
    # u FAQAT shtamp o'zgarganda ishga tushadi (main.py:
    # "if not _schema_ready()"). Shtamp esa oxirgi migratsiyadan
    # quriladi. Ya'ni migratsiyasiz yangi jadval qo'shilsa, u jonli
    # bazada UMUMAN yaratilmasdi va bo'lim 500 bergan bo'lardi.
    # Shu qator aynan shuning uchun turibdi.
    ("0013_lead_delete_reason", [
        "CREATE INDEX IF NOT EXISTS ix_leads_deleted_reason "
        "ON leads_deleted (reason)",
        "CREATE INDEX IF NOT EXISTS ix_leads_deleted_at "
        "ON leads_deleted (deleted_at)",
    ]),
    # 2026-09-03: daraja stavkasi tarixi (teacher_grade_rates). Jadval
    # create_all orqali yaratiladi — bu qator SCHEMA_STAMP ni ko'tarib,
    # jonli bazada create_all ishlashini ta'minlaydi (yangi jadval ham
    # migratsiya talab qiladi, aks holda hech qachon yaratilmaydi).
    ("0014_grade_rate_history", [
        "CREATE INDEX IF NOT EXISTS ix_tgr_grade_eff "
        "ON teacher_grade_rates (grade_key, effective_from)",
    ]),
    # 2026-09-07 (Jahongir: "otgan oy muhransin"): oylik muhri
    # (payroll_seals). Jadvalni create_all yaratadi — bu qator
    # SCHEMA_STAMP ni ko'tarib, jonli bazada yaratilishini
    # ta'minlaydi (yuqoridagi 0013 izohiga qarang).
    ("0015_payroll_seal", [
        "CREATE INDEX IF NOT EXISTS ix_payroll_seals_period "
        "ON payroll_seals (period)",
    ]),
    # 2026-09-18 (Jahongir: "kahoot korinishidagi oyinlar ... har bir
    # unitda"): jonli o'yin jadvallari (live_games, live_players,
    # live_answers). Jadvalni create_all yaratadi — bu qator shtampni
    # ko'taradi va tez-tez so'raladigan ustunlarga indeks qo'yadi.
    ("0016_live_games", [
        "CREATE INDEX IF NOT EXISTS ix_live_answers_game_q "
        "ON live_answers (game_id, q_index)",
        "CREATE INDEX IF NOT EXISTS ix_live_answers_player_q "
        "ON live_answers (player_id, q_index)",
    ]),
    # 2026-09-18: o'yin guruhga bog'lanadi, o'quvchi ro'yxatdan tanlanadi,
    # coin avtomat (live_games.group_id/exam_id, live_players.student_id/
    # correct_count/coins). Ustunlarni _ensure_new_columns qo'shadi.
    ("0017_live_games_group_coins", [
        "CREATE INDEX IF NOT EXISTS ix_live_players_student "
        "ON live_players (student_id)",
    ]),
    # 2026-09-18: dars boshqaruvi — group_plans, lesson_runs (jadvalni
    # create_all yaratadi; bu qator shtampni ko'taradi).
    ("0018_lesson_runs", [
        "CREATE INDEX IF NOT EXISTS ix_lesson_runs_lesson "
        "ON lesson_runs (lesson_id)",
    ]),
    # 2026-09-18: topshiriqlar (assignments, assignment_submissions,
    # assignment_media) — create_all yaratadi; shtamp ko'tariladi.
    ("0019_assignments", [
        "CREATE INDEX IF NOT EXISTS ix_asub_assignment_student "
        "ON assignment_submissions (assignment_id, student_id)",
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
