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
    # 2026-09-27: mock qat'iy rejimi — chiqishlar eid'lari (bir chiqish
    # ikki marta sanalmasin). Avtomat qo'riqchi ham qo'shadi, lekin
    # jonli loglarda buni tasdiqlab bo'lmadi — shu qator kafolat
    # (ustun bo'lsa "duplicate column" bilan o'tib ketadi).
    ("0020_exam_away_eids", [
        "ALTER TABLE exam_submissions ADD COLUMN away_eids TEXT",
    ]),
    # 2026-09-28: Writing AI bahosi (writing_ai.py) — avtomat qo'riqchi
    # ham qo'shadi, lekin loglarda tasdiqlab bo'lmaydi; shu kafolat.
    ("0021_writing_ai", [
        "ALTER TABLE exam_submissions ADD COLUMN ai_status VARCHAR",
        "ALTER TABLE exam_submissions ADD COLUMN ai_score FLOAT",
        "ALTER TABLE exam_submissions ADD COLUMN ai_review TEXT",
        "ALTER TABLE exam_submissions ADD COLUMN paper_by VARCHAR",
        "ALTER TABLE mock_practice ADD COLUMN ai_review TEXT",
    ]),
    # 2026-09-30: guruh arxivi (bo'sh guruhlar ro'yxatdan yashiriladi)
    ("0022_group_archive", [
        "ALTER TABLE groups ADD COLUMN archived_at TIMESTAMP",
        "ALTER TABLE groups ADD COLUMN archived_by VARCHAR",
        "ALTER TABLE groups ADD COLUMN archive_note VARCHAR",
    ]),
    ("0023_exam_report_owner", [
        "ALTER TABLE exams ADD COLUMN report_teacher_id INTEGER",
        "ALTER TABLE exams ADD COLUMN report_branch_id INTEGER",
        "UPDATE exams SET report_teacher_id = (SELECT teacher_id FROM groups WHERE groups.id = exams.group_id), "
        "report_branch_id = (SELECT branch_id FROM groups WHERE groups.id = exams.group_id)",
    ]),
    # 2026-10-02: imtihon buyurtmasida vaqtni ko'chirish taklifi
    ("0024_exam_order_reschedule", [
        "ALTER TABLE exam_orders ADD COLUMN proposed_date DATE",
        "ALTER TABLE exam_orders ADD COLUMN proposed_time VARCHAR",
        "ALTER TABLE exam_orders ADD COLUMN proposed_by INTEGER",
        "ALTER TABLE exam_orders ADD COLUMN proposed_at TIMESTAMP",
        "ALTER TABLE exam_orders ADD COLUMN proposed_reason VARCHAR",
        "ALTER TABLE exam_orders ADD COLUMN proposed_note TEXT",
        "ALTER TABLE exam_orders ADD COLUMN proposed_from_status VARCHAR",
    ]),
    # 2026-10-02: xodim oyligi qaysi oy uchun berilgani (oy yopilishi)
    ("0025_expense_period", [
        "ALTER TABLE expenses ADD COLUMN period VARCHAR",
    ]),
    # 2026-10-08: nomzod suhbat varaqasi (interview_sheets) — jadvalni
    # create_all yaratadi; bu qator shtampni ko'taradi.
    ("0026_interview_sheets", [
        "CREATE INDEX IF NOT EXISTS ix_interview_sheets_cand_author "
        "ON interview_sheets (candidate_id, author_id)",
    ]),
    # 2026-10-08: HR tahrirlagan suhbat savollari (interview_guide_config)
    ("0027_interview_guide_config", [
        "SELECT 1",
    ]),
    # 2026-10-12: Ustozlar oyligida guruh qatoriga "To'landi" — ustoz
    # to'lovi qaysi guruh uchun (common._teacher_pay_alloc). Jahongir:
    # "men oylikni to'lagan bo'lsa ham xarajatlar bo'limida oylikni
    # tanlab shu joyda to'lanmagan bo'lib turibdi".
    ("0028_teacher_payment_group", [
        "ALTER TABLE teacher_payments ADD COLUMN group_id INTEGER",
    ]),
    # 2026-10-14: o'quvchiga qo'shilgan YANGI guruh avval sinovda
    # (student_groups.status = 'trial'), faollashtirilganda pul yechiladi.
    # Jahongir: "Avval qo'shilganda sinovda bo'lishi kerak keyin
    # faollashtirilsa pul yechsin". Mavjud bog'lanishlarning hammasi
    # 'active' — ular allaqachon hisoblanib kelgan, hech narsa o'zgarmaydi.
    ("0029_student_group_trial", [
        "ALTER TABLE student_groups ADD COLUMN status VARCHAR DEFAULT 'active'",
        "ALTER TABLE student_groups ADD COLUMN activated_on DATE",
        "UPDATE student_groups SET status = 'active' WHERE status IS NULL",
    ]),
    # 2026-10-16: Terminal ↔ naqd o'tkazmasi (bank_cash_transfers) —
    # jadvalni create_all yaratadi; bu yerda filial+sana indeksi (kassa
    # qoldig'i shu ikki ustun bo'yicha so'raladi). Jahongir: terminaldan
    # naqd yechish 1% komissiya bilan, naqdni terminalga topshirish.
    ("0030_bank_cash_transfers", [
        "CREATE INDEX IF NOT EXISTS ix_bank_cash_transfers_branch_date "
        "ON bank_cash_transfers (branch_id, date)",
    ]),

    # GURUH BO'YICHA MUZLATISH (2026-10-16, Jahongir: "2ta guruhi bor
    # o'quvchini bir guruhini muzlatsa ikkinchisi ham muzlayabdi,
    # ikkalasi alohida alohida muzlatish kerak"). status='frozen' —
    # shu guruh muzlagan, qolgan guruhlar ishlayveradi (link_freeze.py).
    ("0030_student_group_freeze", [
        "ALTER TABLE student_groups ADD COLUMN frozen_from DATE",
        "ALTER TABLE student_groups ADD COLUMN frozen_until DATE",
        "ALTER TABLE student_groups ADD COLUMN frozen_note VARCHAR",
    ]),

    # 2026-10-16: fan bo'yicha chegirma (discounts.group_id; bo'sh —
    # barcha fanlarga)
    ("0031_discount_group", [
        "ALTER TABLE discounts ADD COLUMN group_id INTEGER",
    ]),

    # 2026-10-16: LUG'AT BANKI ("So'z bilish", 2-qadam, yashirin ishga
    # tushirish). Jahongir: har 1000 talik so'z darajasini tugatgan
    # o'quvchiga N coin, so'z bilish jadvali (OWNER_DECISIONS D1–D5).
    # Faqat QO'SHADI, hech narsani o'zgartirmaydi va o'chirmaydi.
    #
    # Olti jadvalni (wordbank_words, wordbank_student_words,
    # wordbank_sessions, wordbank_session_items, wordbank_band_awards,
    # wordbank_size_tests) models.py dagi modellardan create_all
    # yaratadi — bu qator shtampni ko'taradi (0013 izohiga qarang),
    # shuning uchun jonli bazada create_all albatta ishlaydi. Xom
    # CREATE TABLE yozilmadi: SQLite va Postgres'da avto-raqam
    # sintaksisi har xil, model esa ikkalasida ham to'g'ri yaratadi.
    #
    # UNIQUE ux_wordbank_band_awards — pul himoyasi: model cheklovi
    # bo'lmay qolgan holatda ham (masalan jadval oldinroq qisman
    # yaratilgan bo'lsa) bitta daraja uchun ikki marta coin yozilmaydi.
    ("0032_wordbank", [
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_wordbank_band_awards "
        "ON wordbank_band_awards (student_id, band)",
        "CREATE INDEX IF NOT EXISTS ix_wordbank_words_band_rank "
        "ON wordbank_words (band, rank)",
        "CREATE INDEX IF NOT EXISTS ix_wordbank_sw_student_due "
        "ON wordbank_student_words (student_id, due)",
        "CREATE INDEX IF NOT EXISTS ix_wordbank_sessions_student "
        "ON wordbank_sessions (student_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_wordbank_size_tests_student "
        "ON wordbank_size_tests (student_id, created_at)",
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
        print("[migratsiya] %s: %s" % (version, err or "ok"))
        results.append((version, err))
        if err:
            try:
                db.add(models.ErrorLog(
                    path="migration", method=version, detail=err))
                db.commit()
            except Exception:
                db.rollback()
    return results
