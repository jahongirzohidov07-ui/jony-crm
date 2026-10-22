"""Jony Academy tashkiliy rollari va ruxsatlar matritsasi.

Ichki kalitlar (masalan "founder") bazada saqlanadi va hech qachon
o'zgarmasligi kerak; ekranda ko'rinadigan nom UZ_LABELS'da turadi.

Ruxsatlar ikki qavatli:
  1) Bu fayldagi ro'yxatlar - STANDART holat, kod bilan keladi.
  2) RolePermission jadvali - ASOSCHI o'zgartirgan holat, bazada turadi.
Ikkinchisi birinchisini bosadi. Asoschining huquqini esa hech kim,
hatto asoschining o'zi ham, olib tashlay olmaydi - aks holda tizimga
kirish yo'li yopilib qolardi.
"""

# ---- Rahbariyat -------------------------------------------------------
FOUNDER = "founder"                     # Asoschi - to'liq huquq
FINANCE_DIRECTOR = "finance_director"   # Moliya direktori
ACCOUNTANT = "accountant"               # Buxgalter
BRANCH_MANAGER = "branch_manager"       # Filial rahbari
# HAMKOR MARKAZ RAHBARI (2026-09-17, Jahongir: "Stetchga doir barcha
# narsa va funksiyalar moliyaviy hammasi ochiladigan bolsin").
# Bu HAQIQIY rol emas — VIRTUAL belgi: asosiy filiali hamkor markaz
# (Stech) bo'lgan filial rahbari. Ro'yxatga qo'shilsa, o'sha amal unga
# ham ochiladi (auth.has_role). Ma'lumoti baribir faqat o'z filiali
# bilan cheklanadi — u ORG_WIDE emas.
PARTNER_HEAD = "partner_head"

# ---- Sotuv va marketing ----------------------------------------------
SALES_HEAD = "sales_head"               # Sotuv rahbari
SALES_MANAGER = "sales_manager"         # Sotuv menejeri
ADMINISTRATOR = "administrator"         # Administrator (qabul, kassa)
SMM_MANAGER = "smm_manager"             # Marketolog / SMM

# ---- O'quv bo'limi ----------------------------------------------------
ACADEMIC_HEAD = "academic_head"         # O'quv bo'limi rahbari
TEACHER = "teacher"                     # O'qituvchi
SUPPORT_TEACHER = "support_teacher"     # Support teacher
HEAD_SUPPORT = "head_support"           # Support teacherlar boshlig'i
EXAMINER = "examiner"                   # Examiner
HEAD_EXAMINER = "head_examiner"         # Examinerlar boshlig'i

# ---- Qo'llab-quvvatlash ----------------------------------------------
HR_MANAGER = "hr_manager"               # HR menejer
FACILITY_MANAGER = "facility_manager"
EVENT_MANAGER = "event_manager"         # Tadbirlar menejeri (event manager)   # Xo'jalik ishlari menejeri

# ---- Tashqi foydalanuvchilar -----------------------------------------
PARENT = "parent"                       # Ota-ona
STUDENT = "student"                     # O'quvchi

# ---- Kuzatuvchi (2026-10-19) -------------------------------------------
# Jahongir: "kuzatuvchi rolidan barcha agentlar kirib o'ziga kerakli
# ma'lumotlarni olishi mumkin bo'lsin". Maslahat kengashi (AI agentlar)
# shu hisob bilan kiradi.
#
# Qanday ishlaydi (auth.get_current_user):
#   - KO'RISH so'rovlari (GET/HEAD) asoschi ko'zi bilan ishlaydi —
#     barcha filial, barcha bo'lim, barcha hisobot;
#   - har qanday O'ZGARTIRISH (POST/PUT/PATCH/DELETE) 403 bilan
#     to'xtatiladi — bitta umumiy joyda, endpointlarning o'zida emas;
#   - butun bazani yoki shaxsiy hujjatlarni chiqaradigan bir nechta
#     yo'l (OBSERVER_DENY_PREFIXES) ko'rishda ham yopiq.
# Xodim emas: ish haqi yo'q, xodimlar ro'yxatlarida chiqmaydi
# (EXTERNAL_ROLES). Rolni faqat asoschi beradi. Qo'shimcha lavozim
# sifatida ishlamaydi — faqat ASOSIY lavozim bo'lsa kuchga kiradi.
OBSERVER = "observer"

ALL_ROLES = [
    FOUNDER,
    FINANCE_DIRECTOR,
    ACCOUNTANT,
    BRANCH_MANAGER,
    SALES_HEAD,
    SALES_MANAGER,
    ADMINISTRATOR,
    SMM_MANAGER,
    ACADEMIC_HEAD,
    TEACHER,
    SUPPORT_TEACHER,
    HEAD_SUPPORT,
    EXAMINER,
    HEAD_EXAMINER,
    HR_MANAGER,
    FACILITY_MANAGER,
    EVENT_MANAGER,
    PARENT,
    STUDENT,
    OBSERVER,
]

UZ_LABELS = {
    FOUNDER: "Asoschi",
    FINANCE_DIRECTOR: "Moliya direktori",
    ACCOUNTANT: "Buxgalter",
    BRANCH_MANAGER: "Filial rahbari",
    SALES_HEAD: "Sotuv rahbari",
    # Markaz tilida "Administrator" deganda SOTUV MENEJERI tushuniladi
    SALES_MANAGER: "Administrator",
    ADMINISTRATOR: "Administrator (qabul)",
    SMM_MANAGER: "Marketolog / SMM",
    ACADEMIC_HEAD: "O'quv bo'limi rahbari",
    TEACHER: "O'qituvchi",
    SUPPORT_TEACHER: "Support teacher",
    HEAD_SUPPORT: "Support teacherlar boshlig'i",
    EXAMINER: "Examiner",
    HEAD_EXAMINER: "Examinerlar boshlig'i",
    HR_MANAGER: "HR menejer",
    FACILITY_MANAGER: "Xo'jalik ishlari menejeri",
    EVENT_MANAGER: "Event menejer (tadbirlar)",
    PARENT: "Ota-ona",
    STUDENT: "O'quvchi",
    OBSERVER: "Kuzatuvchi (faqat ko'rish)",
}

# Rollarni guruhlab ko'rsatish - 18 ta rolni bir ro'yxatda ko'rsatish
# o'qishga og'ir.
ROLE_GROUPS = [
    ("leadership", "Rahbariyat",
     [FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, BRANCH_MANAGER]),
    ("sales", "Sotuv va marketing",
     [SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, SMM_MANAGER]),
    ("academic", "O'quv bo'limi",
     [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
      EXAMINER, HEAD_EXAMINER]),
    ("support", "Qo'llab-quvvatlash", [HR_MANAGER, FACILITY_MANAGER, EVENT_MANAGER]),
    ("external", "Tashqi", [PARENT, STUDENT, OBSERVER]),
]

# Tashqi foydalanuvchilar - ular xodim emas, ish haqi ham yo'q,
# xodimlar ro'yxatida ham chiqmaydi.
EXTERNAL_ROLES = [PARENT, STUDENT, OBSERVER]

# Kuzatuvchi ko'rish so'rovlarini shu rol ko'zi bilan bajaradi.
OBSERVER_VIEW_AS = FOUNDER
# Kuzatuvchiga ruxsat etilgan yagona yozish amallari — o'z hisobi.
# Standart parol ("jonyjony") birinchi kirishda almashtirilishi shart.
OBSERVER_WRITE_ALLOW = ("/api/auth/me/password",)
# Ko'rishda ham yopiq: butun baza zaxirasi, eksport, fayllar (pasport,
# shartnoma nusxalari), xodim hujjatlari, qora ro'yxat, xato loglari.
OBSERVER_DENY_PREFIXES = (
    "/api/backup",
    "/api/placement/export",
    "/api/attachments",
    "/api/hr/documents",
    "/api/hr/blacklist",
    "/api/errors",
)
STAFF_ROLES = [r for r in ALL_ROLES if r not in EXTERNAL_ROLES]

# ---- Ruxsat guruhlari -------------------------------------------------
# Bular STANDART holat. Asoschi ruxsatlar matritsasidan o'zgartirsa,
# baza jadvalidagi qiymat ustun turadi.

# Kundalik operatsion to'liq huquq.
FULL_ACCESS = [FOUNDER, BRANCH_MANAGER]
# Guruh ochish/tahrirlash — o'quv bo'limi rahbari ham qiladi: guruhlar
# uning bevosita ishi (dars sifati, jadval, ustoz biriktirish).
GROUP_MANAGE = [FOUNDER, BRANCH_MANAGER, ACADEMIC_HEAD]

# Talaba yozuvlari bilan ishlaydiganlar.
TEACHING_STAFF = FULL_ACCESS + [
    SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, TEACHER, SUPPORT_TEACHER,
    HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER, ACADEMIC_HEAD,
]

# Xodimlar ro'yxatini KO'RA oladiganlar.
STAFF_VIEWERS = FULL_ACCESS + [HR_MANAGER, FINANCE_DIRECTOR]

# Xodim yaratish va ROL BERISH - faqat asoschi. Bu ataylab eng tor
# guruh: rol berish tizimdagi eng xavfli amal.
USER_ADMIN = [FOUNDER]

# Moliya (foyda-zarar, xarajat, ish haqi).
FINANCE_ACCESS = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT]

# PUL OQIMI VA XARAJATLAR — ADMINISTRATORGA HAM (2026-08-10, Jahongir:
# "administratorlarga cashflow bo'limini ochib ber va xarajatlarni
# kirgizishni ham ochib ber").
#
# Administrator kunlik kassa bilan ishlaydi — kirim-chiqimni u
# ko'radi va mayda xarajatni (masalan suv, kanselyariya) o'zi
# kiritadi. Foyda-zarar, budjet va oyliklar esa unga OCHILMADI —
# ular boshqacha darajadagi ma'lumot.
CASHFLOW_ACCESS = FINANCE_ACCESS + [ADMINISTRATOR, SALES_MANAGER]
# CHEKLANGAN FILIALLAR (2026-10-06, Jahongir: "shu cashflow adminlarga
# ko'rinmasin, Zafar filialidagilarga. Ularga faqat bugun urilgan pullar
# va umumiy hisobi ko'rinsin. Qolgan filial turaversin"). Shu filial
# administratori Pul oqimida faqat BUGUNGI tushumni ko'radi — oylik
# kassa daftari, kirim/chiqim/kassa qoldig'i va trend yopiq. Filial
# nomida shu so'z bo'lsa yetadi (katta-kichik harf farqsiz).
CASHFLOW_LIMITED_BRANCHES = ("zafar",)
CASHFLOW_LIMITED_ROLES = [ADMINISTRATOR, SALES_MANAGER]
# Xarajat KIRITISH va tahrirlash. O'CHIRISH ataylab bunga kirmaydi
# (pastdagi EXPENSE_DELETE) — kiritilgan xarajatni o'chirish pul
# hisobotini o'zgartiradi, shuning uchun moliyada qoladi.
EXPENSE_ACCESS = FINANCE_ACCESS + [ADMINISTRATOR, SALES_MANAGER]
EXPENSE_DELETE = FINANCE_ACCESS

# TERMINAL ↔ NAQD O'TKAZMASI (2026-10-16, Jahongir: terminaldagi pulni
# bankdan naqd yechish — bank 1% oladi, naqdga sof summa tushadi; naqdni
# terminalga topshirish — komissiyasiz). Pul oqimi bilan bir xil:
# administrator o'z filialida kiritadi va ko'radi. Tahrirlash, o'chirish
# va qoldiqdan oshiq summani "baribir saqlash" — faqat rahbariyat/moliya
# (xarajat o'chirishdagi kabi). Komissiya foizi butun markaz uchun bitta —
# uni faqat asoschi va moliya xodimlari o'zgartiradi.
# Faqat shu ikki tur bor: egasiga foyda yechish turi ataylab YO'Q
# (Jahongir, 2026-10-16: o'quv markazda bunday yechim bo'lmaydi).
BANK_TRANSFER_ACCESS = list(CASHFLOW_ACCESS)
BANK_TRANSFER_MANAGE = list(FINANCE_ACCESS)
BANK_FEE_RATE_EDIT = [FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT]
BANK_TRANSFER_KINDS = [
    ("withdraw", "Terminaldan naqdga"),
    ("deposit", "Naqd → terminalga"),
]
BANK_TRANSFER_KIND_LABELS = dict(BANK_TRANSFER_KINDS)
# Standart komissiya foizi; haqiqiy qiymat Sozlamada
# (integration_settings: bank_withdraw_fee_percent).
BANK_WITHDRAW_FEE_DEFAULT = 1.0
BANK_WITHDRAW_FEE_MAX = 10.0

# QO'SHIMCHA DAROMAD (2026-10-06): administrator kiritadi va tuzatadi,
# arxivlash (o'chirish o'rniga) — faqat moliya, xarajatdagi kabi.
OTHER_INCOME_ACCESS = FINANCE_ACCESS + [ADMINISTRATOR, SALES_MANAGER]
OTHER_INCOME_ARCHIVE = FINANCE_ACCESS
OTHER_INCOME_CATEGORY_DEFS = [
    ("book_sale", "Kitob / qo'llanma sotuvi"),
    ("mock_exam", "Mock imtihon"),
    ("certificate", "Sertifikat"),
    ("rent", "Ijara (xona, joy)"),
    ("event", "Tadbir / lager"),
    ("merch", "Forma / mahsulot sotuvi"),
    ("other", "Boshqa"),
]
OTHER_INCOME_CATEGORIES = [k for k, _ in OTHER_INCOME_CATEGORY_DEFS]

# Kassa: pul qabul qilish, qarzdorlar bilan ishlash, to'lov foizi.
# Administrator va sotuv menejeri shu ishni qiladi — lekin FOYDANI
# ko'rmaydi. Shuning uchun bu FINANCE_ACCESS dan alohida turadi.
CASH_ACCESS = FINANCE_ACCESS + [SALES_HEAD, SALES_MANAGER, ADMINISTRATOR]

# Lidlar (sotuv voronkasi).
LEAD_ACCESS = FULL_ACCESS + [
    SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, SMM_MANAGER, SUPPORT_TEACHER,
]

# Faqat umumiy statistikani ko'radiganlar.
DASHBOARD_ONLY = [SMM_MANAGER]

# Butun tashkilot bo'yicha ko'radigan rollar (filialga bog'lanmagan).
# MASHQ (TEST) FILIALINI TANLAGICHDA KO'RADIGANLAR
#
# 2026-08-31, Jahongir: "test filial HR rahbariga ko'rinsin, u
# ishlatib ko'radi tekshiradi".
#
# Asoschi hammasini ko'radi (u alohida tekshiriladi). HR rahbari
# xodimlarni o'rgatadi va yangi bo'limlarni sinaydi — mashq
# filiali unga kerak.
#
# Bu ro'yxat FAQAT ko'rinishga ta'sir qiladi. Test filialining
# soxta raqamlari umumiy yig'indiga baribir qo'shilmaydi.
TEST_BRANCH_VIEW = [HR_MANAGER]

ORG_WIDE_ROLES = [
    FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, HR_MANAGER, SMM_MANAGER,
    ACADEMIC_HEAD, SALES_HEAD, HEAD_EXAMINER, HEAD_SUPPORT,
    FACILITY_MANAGER, EVENT_MANAGER,
]

# ---- To'lov usullari --------------------------------------------------
# Cashflow hisoboti shu bo'yicha bo'linadi. Faqat kirim ("payment")
# yozuvlarida ma'noga ega; hisoblangan to'lov va chegirmada bo'sh qoladi.
PAYMENT_METHODS = [
    "cash",      # Naqd
    "card",      # Plastik - Click, Payme, karta o'tkazmasi
    "terminal",  # Terminal - do'kondagi POS apparati
    "other",     # Boshqa
]

PAYMENT_METHOD_LABELS = {
    "cash": "Naqd",
    "card": "Click",
    "terminal": "Terminal",
    "other": "Boshqa",
}

# ---- Xarajatlar: guruh (tur) va kategoriya -----------------------------
# Xarajat ikki qavatli: har bir kategoriya bitta GURUHGA tegishli.
# Hisobot va analitika guruh kesimida chiqadi, kiritish esa aniq
# kategoriya bilan - shunda "kommunalga qancha ketdi" ham, "elektrga
# qancha ketdi" ham bir xil ma'lumotdan chiqadi.

EXPENSE_GROUPS = [
    ("rent", "Ijara"),
    ("communal", "Kommunal"),
    ("office", "Ofis xarajatlari"),
    # 2026-10-02, Jahongir: "xo'jalik xarajatlarini ham kiritish kerak"
    ("household", "Xo'jalik xarajatlari"),
    ("admin_salary", "Ma'muriy xodim oyliklari"),
    ("teacher_salary", "Ustozlar oyligi"),   # avtomatik - qo'lda kiritilmaydi
    ("marketing", "Reklama"),
    ("tax", "Soliq"),
    ("other", "Boshqa"),
]
EXPENSE_GROUP_LABELS = dict(EXPENSE_GROUPS)

# (kalit, nomi, guruh)
EXPENSE_CATEGORY_DEFS = [
    ("rent", "Ijara", "rent"),

    ("electricity", "Elektr toki", "communal"),
    ("gas", "Gaz", "communal"),
    ("water_main", "Vodoprovod suv", "communal"),
    ("internet", "Internet / aloqa", "communal"),
    # Eski yozuvlar shu kalitda edi - yo'qotmaslik uchun qoldiramiz.
    ("utilities", "Kommunal (umumiy)", "communal"),

    ("cooler_water", "Kuler suvi", "office"),
    ("printer_refill", "Printer zapravka", "office"),
    ("paper", "List qog'oz", "office"),
    ("marker", "Marker / doska", "office"),
    ("stationery", "Boshqa kanstovar", "office"),
    ("equipment", "Jihoz", "office"),
    # 2026-08-12, Jahongir: "ichiga ishxona telefoni uchun ham alohida,
    # kitobga alohida, vlajniy alohida tanlaydigan bo'lsin".
    ("wet_wipes", "Vlajniy salfetka", "office"),
    ("book", "Kitob", "office"),
    ("office_phone", "Ishxona telefoni", "communal"),

    ("cleaning", "Tozalash vositalari", "household"),
    ("hygiene", "Gigiyena (sovun, tualet qog'oz)", "household"),
    ("kitchen", "Choy, shakar, oshxona", "household"),
    ("household", "Boshqa xo'jalik mollari", "household"),

    ("admin_salary", "Ma'muriy xodim oyligi", "admin_salary"),
    ("support_salary", "Farrosh / qorovul", "admin_salary"),
    # 2026-10-02, Jahongir: budjetda "Asoschi oylik deb ham qo'shasan"
    ("founder_salary", "CEO oyligi", "admin_salary"),  # "CEO oyligi deylik, Asoschi emas"
    # Eski "salary" kaliti ham ma'muriy xodimlarni bildirgan.
    ("salary", "Xodimlar oyligi (eski)", "admin_salary"),

    ("ads", "Reklama", "marketing"),
    ("tax", "Soliq", "tax"),
    ("repair", "Ta'mir", "other"),
    # 2026-10-16, Jahongir: terminaldagi pulni naqdga yechganda bank 1%
    # oladi — bu haqiqiy xarajat. Qo'lda KIRITILMAYDI: "Terminaldan naqd
    # yechish" o'tkazmasi o'zi bitta xarajat qatorini yozadi (pastdagi
    # EXPENSE_AUTO_CATEGORIES), P&L da bir marta ko'rinadi.
    ("bank_fee", "Bank komissiyasi (1%)", "other"),
    ("other", "Boshqa", "other"),
]

EXPENSE_CATEGORIES = [c for c, _, _ in EXPENSE_CATEGORY_DEFS]
# Faqat avtomat yoziladigan xarajat turlari (2026-10-16): Xarajatlar
# formasidan kiritib/tahrirlab/o'chirib bo'lmaydi — manbasi orqali
# (bank_fee — Terminal ↔ naqd o'tkazmasi) o'zgaradi, aks holda komissiya
# ikki marta yoki o'tkazmasiz qolib ketardi.
EXPENSE_AUTO_CATEGORIES = ["bank_fee"]

# SONI so'raladigan xarajatlar. "3 ta vlajniy 45 000 so'm" deb yozilsa,
# keyin "oyiga nechta marker ketyapti" degan savolga javob bor
# (Jahongir, 2026-08-12: "keyin sonini qoshadigan bo'lsin").
EXPENSE_COUNTABLE = [
    "book", "wet_wipes", "paper", "marker", "stationery",
    "cooler_water", "printer_refill",
]
# Oylik sifatida yoziladigan kategoriyalar — ular "Oylik" yo'lidan
# keladi va xodimga bog'lanadi.
EXPENSE_SALARY_CATEGORIES = ["admin_salary", "support_salary", "salary"]
EXPENSE_CATEGORY_LABELS = {c: lbl for c, lbl, _ in EXPENSE_CATEGORY_DEFS}
EXPENSE_CATEGORY_GROUP = {c: g for c, _, g in EXPENSE_CATEGORY_DEFS}

# BUDJETDA XODIM OYLIGI BITTALAB (2026-10-02, Jahongir: "ustozlar
# oyligidan tashqari boshqa xodimlar oyligini bitta bitta kiritadigan
# qilish kerak"). Budjet qatori kategoriyasi "staff:<user_id>".
BUDGET_STAFF_PREFIX = "staff:"
# Ustozlar bo'limidagi faqat-reja qatorlari (2026-10-02, Jahongir:
# "ustoz bonuslari deb qo'shib qo'y").
BUDGET_TEACHER_CATS = {"teacher_bonus": "Ustoz bonuslari"}


def budget_category_group(cat):
    """Budjet kategoriyasining xarajat guruhi (staff:* — ma'muriyat)."""
    if cat and str(cat).startswith(BUDGET_STAFF_PREFIX):
        return "admin_salary"
    if cat in BUDGET_TEACHER_CATS:
        return "teacher_payroll"
    return EXPENSE_CATEGORY_GROUP.get(cat, "other")

# DIQQAT: ustozlar ish haqi bu ro'yxatda YO'Q - u TeacherPayout
# jadvalidan avtomatik olinadi. Agar uni qo'lda ham kiritsangiz,
# P&L'da ikki marta hisoblanib ketadi.

# ---- Lid voronkasi ----------------------------------------------------
LEAD_STAGES = [
    "new",              # Yangi (so'rov keldi, hali bog'lanilmagan)
    "contacted",        # Bog'lanildi
    "trial_scheduled",  # Sinov darsiga yozildi - GURUHGA qo'shiladi
    "trial_attended",   # Sinovga keldi - ustoz yoqlama qo'ygan
    "no_show",          # Sinovga kelmadi     (yo'qotish)
    "converted",        # O'quvchiga aylandi  (yutuq - doskadan chiqadi)
    "rejected",         # Rad etdi            (yo'qotish)
]

LEAD_STAGE_LABELS = {
    "new": "Yangi so'rov",
    "contacted": "Bog'lanildi",
    "trial_scheduled": "Sinovga yozildi",
    "trial_attended": "Sinovga keldi",
    "no_show": "Sinov darsiga kelmadi",
    "converted": "O'quvchi bo'ldi",
    "rejected": "Rad etdi",
}

# Kanban doskasida ko'rinadigan ustunlar. "converted" YO'Q: o'quvchiga
# aylangan odam endi lid emas, u Talabalar bo'limida turadi.
LEAD_BOARD_STAGES = [
    "new", "contacted", "trial_scheduled", "trial_attended",
    "no_show", "rejected",
]

# Voronka hisobida ketma-ketlik (yo'qotish bosqichlari kirmaydi).
LEAD_FUNNEL_ORDER = [
    "new", "contacted", "trial_scheduled", "trial_attended", "converted",
]

# ---- Sinovdan faol o'quvchiga o'tish ----------------------------------
# Sinov darsiga shuncha marta kelgan o'quvchi AVTOMAT faollashadi.
# Yoki shundan oldin to'lov qilsa - to'lov kuni faollashadi.
# Ikkala holatda ham faollashish sanasi - BIRINCHI kelgan kuni: shundan
# hisob-kitob boshlanadi, aks holda bepul o'qigan kunlar yo'qoladi.
TRIAL_LESSONS_TO_ACTIVATE = 3

LEAD_SOURCES = [
    "visit",      # Tashrif - o'zi kirib kelgan
    "phone",      # Telefon - o'zi qo'ng'iroq qilgan
    "instagram",
    "telegram",
    # 2026-08-13, Jahongir: "saytimizga ariza qoldirsa avtomat JonyOS
    # ga ... lid bolib tushsin va manbasi website bo'ladigan qil"
    "website",    # Sayt (jonyacademy.uz) formasi
    "referral",   # Tanish orqali (qo'lda kiritilgan)
    # 2026-08-28, Jahongir: "o'quvchiga maxsus link beriladi ... shu
    # link orqali ... adminlarga so'rov boradi yangi lid bo'lib".
    # ALOHIDA manba: "tanish orqali" bilan aralashsa, referal
    # dasturining haqiqiy samarasi ko'rinmay qoladi.
    "app_referral",  # Do'st taklifi (Jony Student ilovasi havolasi)
    "ads",        # Reklama
    "other",      # Boshqa
]

# Manba lidni voronkaning qaysi nuqtasiga qo'yishini belgilaydi.
LEAD_SOURCE_DEFAULT_STAGE = {
    "visit": "trial_scheduled",
    "phone": "contacted",
    "instagram": "new",
    "telegram": "new",
    "website": "new",
    "referral": "new",
    "app_referral": "new",
    "ads": "new",
    "other": "new",
}

# ---- Audit log --------------------------------------------------------
# Kim nimani o'zgartirgani. Filial rahbari faqat o'z filialining
# tarixini ko'radi (filtr endpointda), asoschi hammasini.
AUDIT_VIEW = [FOUNDER, BRANCH_MANAGER, FINANCE_DIRECTOR]

# ---- Nozik ma'lumotlar ------------------------------------------------
# Support teacher va o'qituvchi to'lov tafsilotlarini ko'rmaydi:
# ularga o'quvchi qarzdor yoki yo'qligi yetarli, summa emas.
PAYMENT_DETAIL_VIEW = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT,
                                     SALES_HEAD, SALES_MANAGER, ADMINISTRATOR]

# Boshqa xodimning oyligini ko'rish - faqat asoschi va HR.
# O'qituvchi faqat O'ZINING oyligini ko'radi.
SALARY_VIEW_ALL = [FOUNDER, HR_MANAGER, FINANCE_DIRECTOR]

# Umumiy kompaniya foydasi - faqat asoschi va filial rahbari
# (rahbar o'z filiali bo'yicha). Sotuv menejeri ko'rmaydi.
PROFIT_VIEW = FULL_ACCESS + [FINANCE_DIRECTOR]

# Akademik baho qo'yish - faqat o'qituvchilar tarkibi.
# Kassir/sotuv menejeri bahoga tegmaydi.
GRADE_EDIT = FULL_ACCESS + [TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
                            EXAMINER, HEAD_EXAMINER, ACADEMIC_HEAD]

# ---- O'quv bo'limi ----------------------------------------------------
# Ta'lim sifatiga javob beradigan bo'lim: akademik risk, guruh to'lishi,
# xonalar. O'quv bo'limi rahbari butun markaz bo'yicha ko'radi.
ACADEMIC_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, HEAD_SUPPORT]

# ---- Examiner (imtihon nazorati) --------------------------------------
# DIQQAT: Examiner o'quv bo'limiga EMAS, to'g'ridan-to'g'ri asoschiga
# bo'ysunadi. Shuning uchun imtihon moduli Audit bo'limida turadi -
# ta'lim sifatini o'lchayotgan odam o'lchanayotgan bo'limga qaram
# bo'lmasligi kerak.
EXAM_ACCESS = [FOUNDER, EXAMINER, HEAD_EXAMINER]
# Natijani KO'RA oladiganlar (kiritish EXAM_ACCESS'da).
EXAM_VIEW = EXAM_ACCESS + [BRANCH_MANAGER, ACADEMIC_HEAD, TEACHER]

# Testni TASDIQLASH - faqat examiner va asoschi.
EXAM_APPROVE = EXAM_ACCESS
# Imtihonni TAHRIRLASH (sana, nom, unit, maksimal ball) va O'CHIRISH
# (2026-09-17, Jahongir: "examiner testlarni edit qilish va o'chirishni
# examinerlar boshlig'iga qo'shib ber"). Oddiy examiner va ustozda yo'q.
EXAM_EDIT = [FOUNDER, BRANCH_MANAGER, HEAD_EXAMINER]

# ---- Xodimlar mock mashqi (2026-09-27) --------------------------------
# Jahongir: "boshqalar ham o'zi kirib ishlaydigan bo'lsa yaxshi bo'lardi
# mock testni xodimlargayam koproq ustozlarga ular ham experience qilib
# xatolarni aytadida". Sotuv va administratorlar ATAYLAB yo'q: har
# urinish javob kalitlarini ochadi (egasi keyin qo'shishi mumkin).
# src/lib/roles.ts dagi bir xil nomli ro'yxatlar bilan mos bo'lishi shart.
MOCK_PRACTICE = FULL_ACCESS + [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER,
                               HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER]
# Ustozlar: 30 kunda bir variant + javob kalitini cheklab ko'rsatish
# ("ustozlar aynan testga tayyorlash" xavfi — exam_online.mix_parts).
MOCK_LIMITED = [TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT]
# Savol xatolari ro'yxatini ko'radi / tuzatadi
MOCK_ISSUE_VIEW = list(dict.fromkeys(EXAM_ACCESS + EXAM_EDIT))
MOCK_ISSUE_TRIAGE = EXAM_EDIT

# ---- Support teacher --------------------------------------------------
SUPPORT_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, SUPPORT_TEACHER,
                                HEAD_SUPPORT]

# Imtihon tasdiqlash holati.
EXAM_STATUSES = [
    ("draft", "Qoralama"),
    ("approved", "Tasdiqlangan"),
    ("done", "O'tkazildi"),
    ("cancelled", "Bekor qilindi"),
]
EXAM_STATUS_LABELS = dict(EXAM_STATUSES)

# Guruh ta'lim sifati standarti (foizda). Shundan past bo'lgan guruh
# "standartdan ortda" hisoblanadi.
EXAM_STANDARD_PERCENT = 70.0
# Shundan past ball olgan o'quvchiga qayta imtihon tavsiya etiladi.
EXAM_RETAKE_BELOW = 60.0
# Sertifikatga tavsiya uchun eng kam o'rtacha foiz.
CERTIFICATE_RECOMMEND_PERCENT = 85.0

# ---- Support teacher: o'quvchi bilan ishlash --------------------------
SUPPORT_ISSUE_KINDS = [
    ("attendance", "Davomat muammosi"),
    ("homework", "Uy vazifasi muammosi"),
    ("behaviour", "Xulq"),
    ("motivation", "Motivatsiya"),
    ("other", "Boshqa"),
]
SUPPORT_ISSUE_LABELS = dict(SUPPORT_ISSUE_KINDS)

# Davomat shu foizdan past bo'lsa - muammo deb belgilanadi.
SUPPORT_ATTENDANCE_THRESHOLD = 75.0

# ---- Manzillar va maktablar -------------------------------------------
# Zafar filialiga tegishli mahallalar. Qo'lda yozish o'rniga ro'yxatdan
# tanlanadi: shundagina "qaysi mahalladan ko'p o'quvchi kelyapti" degan
# savolga javob bor. Erkin matn bo'lsa statistika chiqmaydi.
ZAFAR_AREAS = [
    "Zafar", "1-savxoz", "Juma", "Qushchi", "Mallaboy", "Nazarboy",
    "Mavlonov", "Avangard", "Oybek", "Agrouchastka", "2-savxoz",
    "Hamza", "Namuna", "To'la", "3-savxoz", "4-savxoz", "5-savxoz",
    "Oxunboboyev",
]

# Filial -> mahallalar. Boshqa filiallarga ro'yxat qo'shilsa shu yerga.
BRANCH_AREAS = {"Zafar": ZAFAR_AREAS}


def areas_for_branch(name: str | None) -> list:
    if name and name in BRANCH_AREAS:
        return BRANCH_AREAS[name]
    # Filial tanlanmagan bo'lsa - hamma mahalla
    out = []
    for lst in BRANCH_AREAS.values():
        for a in lst:
            if a not in out:
                out.append(a)
    return out


# Tumandagi maktablar: 1-60 va bitta ixtisoslashgan.
SCHOOLS = [f"{i}-maktab" for i in range(1, 61)] + ["Ixtisoslashgan maktab"]

# ---- Xodim ishdan bo'shash toifasi ------------------------------------
# "Yashil yo'lak" - yaxshi ajrashildi, qaytarib olish mumkin.
# "Qizil yo'lak" - qayta ishga olinmaydi.
EXIT_TYPES = [
    ("green", "Yashil yo'lak", "Yaxshi ajrashdik — qaytarib olsa bo'ladi"),
    ("neutral", "Neytral", "Oddiy ketish"),
    ("red", "Qizil yo'lak", "Qayta ishga olinmaydi"),
]
EXIT_TYPE_LABELS = {k: lbl for k, lbl, _ in EXIT_TYPES}

# ---- Arxiv toifalari ---------------------------------------------------
# Ketgan o'quvchini pul munosabati bo'yicha uch guruhga ajratamiz -
# kimdan pul olish kerak, kimga qaytarish kerak, kim bilan hisob toza.
ARCHIVE_GROUPS = [
    ("debtor", "Bizdan qarzi bor", "Ular bizga qarzdor"),
    ("credit", "Bizning qarzimiz bor", "Biz ularga qaytarishimiz kerak"),
    ("clear", "Hisob toza", "Hech kimning qarzi yo'q"),
]
ARCHIVE_GROUP_LABELS = {k: lbl for k, lbl, _ in ARCHIVE_GROUPS}

# ---- Dars vaqti --------------------------------------------------------
# Har bir dars 2 soat. Boshlanish vaqti tanlansa tugash avtomat.
LESSON_DURATION_MINUTES = 120
LESSON_START_TIMES = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00",
    "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
]


def lesson_end_time(start: str) -> str:
    """"09:00" -> "11:00". Noto'g'ri qiymatda bo'sh qaytaradi."""
    try:
        h, m = (int(x) for x in start.split(":")[:2])
    except Exception:
        return ""
    total = h * 60 + m + LESSON_DURATION_MINUTES
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def lesson_time_range(start: str | None) -> str:
    if not start:
        return ""
    end = lesson_end_time(start)
    return f"{start} - {end}" if end else start


# ---- Fayl biriktirish -------------------------------------------------
# Fayllar bazada base64 ko'rinishida saqlanadi: alohida fayl xizmati
# kerak emas, lekin shuning uchun hajm cheklangan.
ATTACHMENT_MAX_BYTES = 3 * 1024 * 1024      # 3 MB
ATTACHMENT_KINDS = [
    ("photo", "Rasm"),
    ("certificate", "Sertifikat"),
    ("resume", "Rezyume"),
    ("document", "Hujjat"),
    ("other", "Boshqa"),
]
ATTACHMENT_KIND_LABELS = dict(ATTACHMENT_KINDS)
# Ustoz ham risk ro'yxatini ko'radi - o'z o'quvchisi haqida.
ACADEMIC_VIEW = ACADEMIC_ACCESS + [TEACHER, SUPPORT_TEACHER,
                                   SALES_HEAD, SALES_MANAGER]

# Akademik risk signallari. Har biri ball beradi; ballar yig'indisi
# risk darajasini belgilaydi.
RISK_SIGNALS = [
    ("absent_streak", "Ketma-ket dars qoldirgan", 3),
    ("no_homework", "Uy vazifasini bajarmayapti", 2),
    ("score_drop", "Natijasi tushgan", 3),
    ("payment_late", "To'lovi kechikkan", 2),
    ("complaint", "Ota-onasi shikoyat qilgan", 3),
    ("group_hopping", "Guruhini ko'p almashtirgan", 2),
    ("teacher_negative", "Ustoz salbiy izoh bergan", 2),
    ("no_progress", "Bir necha haftadan beri o'sish yo'q", 2),
]
RISK_SIGNAL_LABELS = {k: lbl for k, lbl, _ in RISK_SIGNALS}
RISK_SIGNAL_WEIGHT = {k: w for k, _, w in RISK_SIGNALS}

# Ball -> daraja. Pastdan yuqoriga tekshiriladi.
RISK_LEVELS = [
    ("normal", "Normal", "green", 0),
    ("watch", "E'tibor kerak", "yellow", 2),
    ("high", "Yuqori xavf", "orange", 5),
    ("critical", "Ketib qolish xavfi", "red", 8),
]
RISK_LEVEL_LABELS = {k: lbl for k, lbl, _, _ in RISK_LEVELS}


def risk_level(score: int) -> str:
    """Ball qaysi darajaga to'g'ri kelishini qaytaradi."""
    out = "normal"
    for key, _lbl, _color, minimum in RISK_LEVELS:
        if score >= minimum:
            out = key
    return out


# Guruh to'lishi (o'quvchi / xona sig'imi).
GROUP_FILL_BANDS = [
    (85, "good", "Yaxshi"),
    (70, "ok", "Qoniqarli"),
    (50, "problem", "Muammoli"),
    (0, "critical", "Birlashtirish yoki yopish"),
]


def fill_band(percent: float) -> tuple:
    for minimum, key, label in GROUP_FILL_BANDS:
        if percent >= minimum:
            return key, label
    return "critical", "Birlashtirish yoki yopish"


# ---- Marketing voronkasi (to'liq yo'l) --------------------------------
# Reklama ko'rilishidan sertifikatgacha. Birinchi ikki bosqich reklama
# platformasidan keladi (qo'lda yoki API orqali kiritiladi), qolganlari
# tizimning o'z ma'lumotidan hisoblanadi.
MARKETING_JOURNEY = [
    ("impressions", "Reklama ko'rildi", "ad"),
    ("clicks", "Bosildi", "ad"),
    ("leads", "Murojaat qoldirildi", "crm"),
    ("contacted", "Bog'lanildi", "crm"),
    ("trial", "Testga keldi", "crm"),
    ("sold", "Sotildi", "crm"),
    ("month1", "1 oy qoldi", "crm"),
    ("month3", "3 oy qoldi", "crm"),
    ("certificate", "Sertifikat oldi", "crm"),
]

CERTIFICATE_KINDS = [
    ("ielts", "IELTS"),
    ("cefr", "CEFR"),
    ("internal", "Ichki sertifikat"),
    ("course", "Kurs tugatdi"),
    ("olympiad", "Olimpiada"),
    ("other", "Boshqa"),
]
CERTIFICATE_KIND_LABELS = dict(CERTIFICATE_KINDS)

# ---- Oilaviy chegirma -------------------------------------------------
# Bir oiladan bir nechta farzand o'qisa chegirma beriladi. Chegirma
# AVTOMAT: biri ketsa ikkinchisiniki o'zidan yo'qoladi, hech kim qo'lda
# olib tashlashi shart emas.
FAMILY_DISCOUNT_MIN_CHILDREN = 2
FAMILY_DISCOUNT_PERCENT = 10.0

# ---- HR (kadrlar) -----------------------------------------------------
# Ishga olish voronkasi. Lid voronkasi bilan bir xil mantiq: nomzod
# bosqichma-bosqich o'tadi, qaysi bosqichda ko'p yo'qotayotganimiz
# ko'rinib turadi.
HR_ACCESS = FULL_ACCESS + [HR_MANAGER]

# NOMZODNI KO'RISH (2026-08-16, Jahongir: "nomzod o'qituvchi bo'lsa
# o'quv bo'limi rahbariga ham ko'rinish kerak. shunda baholay
# olardi").
#
# O'quv bo'limi rahbari sinov darsini baholaydi, lekin HR bo'limining
# hammasini ko'rishi shart emas. Shuning uchun:
#   - ro'yxat va karta OCHIQ, ammo FAQAT USTOZ nomzodlari
#     (buni hr_ats.py dagi _teacher_only_for() cheklaydi);
#   - kartani TAHRIRLASH esa avvalgidek faqat HR_ACCESS'da qoladi.
HR_CANDIDATE_VIEW = HR_ACCESS + [ACADEMIC_HEAD]

VACANCY_STATUSES = [
    ("open", "Ochiq"),
    ("paused", "To'xtatilgan"),
    ("closed", "Yopilgan"),
]

CANDIDATE_STAGES = [
    ("applied", "Ariza topshirdi"),
    ("screening", "Rezyume ko'rildi"),
    ("interview", "Suhbatga chaqirildi"),
    ("demo", "Sinov darsi / vazifa"),
    ("offer", "Taklif berildi"),
    ("hired", "Ishga olindi"),      # yutuq
    ("rejected", "Rad etildi"),     # yo'qotish
]
CANDIDATE_STAGE_LABELS = dict(CANDIDATE_STAGES)

# NOMZOD BOSQICHI -> ISHGA OLISH QUVURI BOSQICHI (2026-08-15).
# Nomzodlar ro'yxati va "Ishga olish quvuri" bir xil odamni ikki xil
# ko'rsatmasligi uchun. Teskari yo'nalish hr_ats.ats_application_move
# ichida allaqachon bor edi.
CANDIDATE_TO_APPLICATION = {
    "applied": "new",
    "screening": "screening",
    "interview": "interview",
    "demo": "demo",
    "offer": "offer",
    "hired": "hired",
    "rejected": "rejected",
    "pool": "pool",
}
# TESKARI XARITA: QUVUR BOSQICHI -> NOMZOD BOSQICHI (2026-08-16).
#
# Quvurda bosqichlar KO'PROQ (telefon suhbati, topshiriq,
# tavsiyanoma tekshiruvi). Nomzodlar ro'yxatida ular yo'q, shuning
# uchun bir nechtasi bitta bosqichga tushadi:
#     phone, interview      -> interview
#     task, demo            -> demo
#     reference, offer      -> offer
#
# Bu xarita ilgari ats_application_move ichida QO'LDA yozilgan edi.
# Ikki joyda ikki nusxa bo'lib qolmasin uchun shu yerga ko'chirildi —
# endi moslikni tekshirish ham shundan foydalanadi.
APPLICATION_TO_CANDIDATE = {
    "new": "applied",
    "screening": "screening",
    "phone": "interview",
    "interview": "interview",
    "task": "demo",
    "demo": "demo",
    "reference": "offer",
    "offer": "offer",
    "hired": "hired",
    "rejected": "rejected",
    "withdrew": "rejected",
    "pool": "rejected",
}


def stages_match(app_stage: str | None, cand_stage: str | None) -> bool:
    """Quvur va nomzod bosqichi BIR XIL holatni bildiradimi?

    Ataylab teskari xarita bo'yicha tekshiriladi. Masalan quvurda
    "Telefon suhbati", nomzodda "Suhbatga chaqirildi" bo'lsa — bu
    NOMUVOFIQLIK EMAS, ikkalasi bir bosqich. Aks holda HR nomzod
    kartasini har saqlaganda quvurdagi nozikroq bosqich yo'qolib,
    "Suhbat"ga tushib qolardi.
    """
    if not app_stage or not cand_stage:
        return False
    return APPLICATION_TO_CANDIDATE.get(app_stage) == cand_stage


CANDIDATE_FUNNEL = [k for k, _ in CANDIDATE_STAGES if k != "rejected"]

CANDIDATE_SOURCES = [
    ("instagram", "Instagram"),
    ("telegram", "Telegram"),
    ("referral", "Tanish orqali"),
    ("job_site", "Ish e'lonlari sayti"),
    ("walk_in", "O'zi keldi"),
    ("alumni", "O'z bitiruvchimiz"),
    ("other", "Boshqa"),
]
CANDIDATE_SOURCE_LABELS = dict(CANDIDATE_SOURCES)

# ---- Marketing --------------------------------------------------------
# Reklama kanallari LID MANBALARI bilan bir xil kalitda: shunda
# "shu kanalga qancha pul ketdi" va "shu kanaldan qancha lid keldi"
# bir joyda taqqoslanadi - CAC shundan chiqadi.
MARKETING_ACCESS = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD]
MARKETING_CHANNELS = LEAD_SOURCES

LEAD_SOURCE_LABELS = {
    "visit": "Tashrif",
    "phone": "Telefon",
    "instagram": "Instagram",
    "telegram": "Telegram",
    "website": "Sayt (jonyacademy.uz)",
    "referral": "Tanish orqali",
    "app_referral": "Do'st taklifi (ilova)",
    "ads": "Reklama",
    "other": "Boshqa",
}
MARKETING_CHANNEL_LABELS = {
    "visit": "Tashrif",
    "phone": "Telefon",
    "instagram": "Instagram",
    "telegram": "Telegram",
    "website": "Sayt",
    "referral": "Tanish orqali",
    "app_referral": "Do'st taklifi (ilova)",
    "ads": "Reklama (boshqa)",
    "other": "Boshqa",
}

# ---- Ijtimoiy tarmoqlar ----------------------------------------------
SOCIAL_PLATFORMS = [("instagram", "Instagram"), ("telegram", "Telegram"),
                    ("youtube", "YouTube")]
# Sahifalarimiz. Telegram ochiq kanal - obunachilar soni avtomat olinadi.
# Instagram uchun rasmiy Graph API tokeni kerak (INSTAGRAM_TOKEN va
# INSTAGRAM_USER_ID muhit o'zgaruvchilari); tokensiz qo'lda kiritiladi.
SOCIAL_HANDLES = {"instagram": "jony_academy", "telegram": "JonyAcademy",
                  "youtube": "jonyacademy"}


# ---- Imtihonlar -------------------------------------------------------
# Bizda asosan unit testlar (12 ta unit), ularga qo'shimcha kurs o'rtasi,
# kurs oxiri va mock testlar bor.
EXAM_KINDS = ["unit", "mid", "end", "mock"]
EXAM_KIND_LABELS = {
    "unit": "Unit test",
    "mid": "Mid-course",
    "end": "End of course",
    "mock": "Mock test",
    # Jonli o'yin natijasi (2026-09-18) — imtihonlar ro'yxatida turadi,
    # lekin EXAM_KINDS ga kirmaydi: qo'lda yaratilmaydi, KPI ga kirmaydi.
    "kahoot": "Kahoot (jonli o'yin)",
}
UNIT_COUNT = 12

# Mock IELTS band'ni foizga o'tkazish uchun eng yuqori band. Coin qoidasi
# hamma test turi uchun foizda ishlashi kerak, shuning uchun band -> foiz:
# 7.0 band => 7/9*100 = 77.8%.
MOCK_MAX_BAND = 9.0

# ---- Coin (gamification) ---------------------------------------------
# Coin qayerdan kelgani. Balans - shu yozuvlar yig'indisi, alohida
# "balans" ustuni yo'q: shunda hech qachon haqiqatdan uzilib qolmaydi.
COIN_SOURCES = ["daily", "exam", "manual", "reward"]
COIN_SOURCE_LABELS = {
    "daily": "Kunlik baho",
    "exam": "Imtihon",
    "manual": "Qo'lda",
    "reward": "Sovg'a",
    "teacher_deduct": "Ustoz ayirdi (intizom)",
    "pay_ontime": "O'z vaqtida to'lov",
    # 2026-10-16: "So'z bilish" — N-daraja (Common N000) to'liq
    # tasdiqlansa N coin, bir marta (Jahongir, OWNER_DECISIONS D1).
    "vocab_band": "So'z bilish: daraja tugatildi",
}

# ---- "So'z bilish": sertifikatni tasdiqlash (2026-10-17) -------------
# Jahongir (OWNER D3, "tasdiqlangandan keyin chiqsin"): o'quvchi yuklagan
# sertifikat natijasi faqat xodim tasdiqlagach ko'rinadi.
# Kim tasdiqlaydi / rad etadi: ustoz (FAQAT o'z guruhlari o'quvchisi),
# filial rahbari va administrator (o'z filiali), o'quv bo'limi rahbari va
# asoschi (butun markaz) — chegara api/wordbank_certs.py da.
# SALES_MANAGER ham shu yerda: markazda "Administrator" deganda aynan shu
# rol tushuniladi (2026-09-03 da hamma administratorlar shunga
# birlashtirilgan — SALARY_PAY izohiga qarang); faqat ADMINISTRATOR
# yozilsa, haqiqiy administratorlar tasdiqlay olmasdi.
# Bekor qilish (tasdiqlangan natijani qaytarib olish) — tor ro'yxat.
# Mukofot yo'q: sertifikat reytingdagi o'ringa ta'sir qilmaydi.
VOCAB_CERT_CONFIRM = FULL_ACCESS + [ACADEMIC_HEAD, ADMINISTRATOR,
                                    SALES_MANAGER, TEACHER]
VOCAB_CERT_REVOKE = FULL_ACCESS + [ACADEMIC_HEAD]
# Imtihon turlari (kalit, yorliq) — src/lib/wordbankApi.ts dagi
# CERT_EXAM_TYPES bilan bir xil.
VOCAB_CERT_EXAM_TYPES = [
    ("ielts", "IELTS"),
    ("multilevel", "CEFR / Multilevel"),
    ("cefr_other", "CEFR (boshqa)"),
    ("sat", "SAT"),
    ("duolingo", "Duolingo"),
    ("toefl", "TOEFL"),
    ("cambridge", "Cambridge"),
    ("topik", "TOPIK"),
    ("goethe", "Goethe"),
    ("torfl", "TORFL"),
    ("other", "Boshqa"),
]
VOCAB_CERT_EXAM_LABELS = dict(VOCAB_CERT_EXAM_TYPES)
VOCAB_CERT_STATUSES = ["pending", "confirmed", "rejected", "withdrawn",
                       "revoked"]
VOCAB_CERT_VERIFY_METHODS = ["asl nusxa ko'rildi", "onlayn tekshirildi",
                             "fayl bo'yicha"]
VOCAB_CERT_REJECT_REASONS = ["fayl o'qilmaydi", "ma'lumot mos emas",
                             "boshqa odamniki", "sertifikat emas", "boshqa"]

# Kunlik baho shkalasi: ustoz har dars uchun 1-5 qo'yadi va o'sha ball
# aynan shuncha coinga teng (foydalanuvchi qoidasi).
DAILY_GRADE_MIN = 1
DAILY_GRADE_MAX = 5

# Imtihon natijasidan coin: foiz shu qiymatdan katta yoki teng bo'lsa,
# eng yuqori mos qator ishlaydi. Bu faqat BOSHLANG'ICH jadval - asoschi
# uni Gamification bo'limidan o'zgartira oladi.
# Jahongirning 2026-08-11 shkalasi: yuqori natija mukofotlanadi,
# past natija coin YECHADI. 65% chegarasi +1 foydasiga.
DEFAULT_EXAM_COIN_RULES = [
    (96.0, 10),
    (86.0, 5),
    (74.0, 3),
    (65.0, 1),
    (60.0, 0),
    (54.0, -1),
    (48.0, -2),
    (42.0, -3),
    (36.0, -5),
    (30.0, -7),
    (24.0, -10),
    (18.0, -15),
    (12.0, -20),
    (0.0, -10),
]

# ---- Ruxsatlar --------------------------------------------------------
# Davomat va imtihon jadvalini ko'rish/yuritish. Administrator (sotuv
# menejeri) ham kiradi: yoqlama hisob-kitobga ta'sir qiladi va uni
# ko'pincha qabuldagi administrator qo'yadi.
# DIQQAT: akademik BAHO bunga kirmaydi - u alohida GRADE_EDIT bilan
# himoyalangan (yuqoriga qarang).
# USTOZ GURUH SONI CHEGARASIDAN OSHISHIGA RUXSATI BORLAR
# (2026-08-10, Jahongir: "HR manager ham guruhlarni to'siqlarsiz
# tahrirlayversin, chunki ba'zi ustozlarda guruhi limitdan oshsa ham
# bemalol saqlayversin").
#
# Chegara o'zi qoladi va ogohlantirish ko'rinadi — faqat bu rollar
# uchun u QAT'IY TAQIQ emas, "baribir saqlash" mumkin bo'lgan
# ogohlantirishga tushadi. Boshqalarda hamon 400 bilan to'xtaydi.
# DIQQAT: bu FAQAT guruh SONI chegarasiga tegishli. Vaqt/xona
# to'qnashuvi (bir vaqtda ikki guruh) hamma uchun taqiqligicha
# qoladi — u jismonan imkonsiz narsa.
# 2026-10-03, Jahongir: "shu joyda baribir ochilsin buyrug'i Stetch filial
# rahbariga ham berilsin" — hamkor markaz rahbari (faqat o'z filialida).
GROUP_LIMIT_OVERRIDE = [FOUNDER, HR_MANAGER, PARTNER_HEAD]

# Faqat O'Z guruhini ko'radigan rollar. Bular uchun guruh, o'quvchi
# va davomat manzil qatoridan ham ochilmaydi — biriktirilmagan guruh
# 403 qaytaradi.
OWN_GROUPS_ONLY = [TEACHER, SUPPORT_TEACHER]

# O'tib ketgan kunning yoqlamasini kim o'zgartira oladi. Ataylab juda
# tor: yoqlama — pul hujjati (ustoz oyligi shundan chiqadi), o'tgan
# kunni istagan odam o'zgartira olsa, oylik ham "o'zgaruvchan" bo'lib
# qoladi. Kelajak kunga esa HECH KIM yoqlama qo'ya olmaydi — bo'lib
# o'tmagan darsni belgilab bo'lmaydi.
PAST_ATTENDANCE = [FOUNDER, ACADEMIC_HEAD]

TEACHING_ACCESS = FULL_ACCESS + [
    TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER,
    SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, ACADEMIC_HEAD,
]
# DARS REJALARI (2026-09-18, Jahongir: "supportlarga kerakmas, examinerlarga
# ham kerakmas, adminlarga ham kerakmas") — ustozlar va rahbariyat.
PLANS_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, TEACHER, SALES_HEAD, SALES_MANAGER]
# Davomat va baholash jurnalini KO'RISH: dars beruvchilar + HR.
# HR belgilay olmaydi (yozish TEACHING_ACCESS/GRADE_EDIT da qoladi),
# faqat xodimlarning darslari qanday ketayotganini kuzatadi.
ATTENDANCE_VIEW = TEACHING_ACCESS + [HR_MANAGER]

# O'QUVCHINING GURUHLARI VA GURUH TARIXI (2026-09-24, Jahongir:
# "hrga o'quvchilar avval qaysi guruhda bo'lgani xozirda qaysi
# guruhda ekani ko'rinsin o'quvchi kartasiga kirganda"). HR davomatni
# allaqachon ko'rardi, lekin guruh kartasi unga yopiq edi va karta
# ochilishi bilan ruxsat xatosi chiqardi.
STUDENT_GROUPS_VIEW = ATTENDANCE_VIEW

# O'QUVCHI KARTASIDAGI IMTIHON TARIXI (2026-09-24, Jahongir:
# "imtixon tarixini o'zgartirish qo'shish tahrirlashni ham qo'sh
# hrga"). Ko'rish - dars beruvchi xodimlar va HR. Tuzatish esa
# guruh varag'idagi bilan BIR XIL ro'yxat: ustoz va support natija
# kirita olmaydi (baholash examinerniki), ularga HR qo'shiladi.
# MASHQ (2026-09-25, Jahongir: "test filialga kirib mashq degan
# bo'lim ochiladi faqat adminlarga"). Topshiradigan — administrator
# (asoschi ham sinab ko'ra oladi). Sozlaydigan — HR va asoschi.
# 2026-09-25 (Jahongir: "admin akkauntidan sinab ko'rdim ... ruxsatingiz
# yo'q deb yozdi"): ro'yxat faqat administrator bilan chegaralangani
# uchun amalda hech kim topshira olmadi — markazda "admin" ishini
# qiladigan xodimning lavozimi boshqacha nomlanishi mumkin. Endi
# ro'yxatda ofisda ishlaydigan barcha lavozimlar bor; ustoz, support
# va examiner yo'q (cheklist ularning ishi emas).
DRILL_TAKE = [ADMINISTRATOR, FOUNDER, BRANCH_MANAGER, SALES_HEAD,
              SALES_MANAGER, ACADEMIC_HEAD, HR_MANAGER]
DRILL_MANAGE = FULL_ACCESS + [HR_MANAGER]

STUDENT_EXAMS_VIEW = TEACHING_STAFF + [HR_MANAGER]
STUDENT_EXAMS_EDIT = [r for r in TEACHING_ACCESS
                      if r not in (TEACHER, SUPPORT_TEACHER)] + [HR_MANAGER]

# Refund: sotuv menejeri SO'RAYDI, filial rahbari yoki moliyachi
# TASDIQLAYDI. Bitta odam ham so'rab ham tasdiqlay olmaydi (asoschidan
# tashqari) — pul qaytarish ikki ko'z ostida bo'ladi.
# Mashqlar bo'yicha INGLIZ TILI darajalari zinasi. Har bir to'g'ri
# javob 1 ball; har daraja uchun PRACTICE_POINTS_PER_LEVEL ball
# yig'ilsa keyingisiga o'tadi. IELTS/CEFR — taxminiy mo'ljal.
PRACTICE_POINTS_PER_LEVEL = 500   # eskirgan (faqat moslik uchun)

# ---------------------------------------------------------------------
#  DARAJA ZINASI VA IELTS BALI (2026-08-25 da qayta qurildi)
#
#  Jahongir: "har bir darajalar orasi 500XP bu juda oson bolib
#  qolyabdi IELTS 6.5 TURGAN QIZGA 72 kunda IELTS 9.0 olasan
#  devoryabsan u faqat grammatika va lugat ishlagan bu tomonda
#  reading listeninglari yoq".
#
#  MUAMMO NIMADA EDI. Daraja ham, IELTS bali ham BITTA umumiy
#  balldan chiqardi va zina chiziqli edi (har 500 ball = keyingi
#  daraja). Ya'ni faqat lug'at o'ynab 3000 ball yig'gan bola
#  "Native / IELTS 9.0" ko'rsatardi — reading va listening umuman
#  yo'q bo'lsa ham.
#
#  ENDI QANDAY. Ikki narsa ajratildi:
#    1) DARAJA (Yo'l xaritasi) — umumiy balldan, lekin zina endi
#       chiziqli emas: yuqoriga chiqqan sari qadam kattalashadi.
#    2) IELTS BALI — har ko'nikma ALOHIDA 0-100 ballga o'giriladi,
#       har biri o'z bandiga aylanadi, umumiy band esa OLTALASINING
#       O'RTACHASI. Reading/listening nol bo'lsa — o'rtacha ham
#       past bo'ladi, bola aldanmaydi.
# ---------------------------------------------------------------------

# Umumiy daraja zinasi: shu darajaga chiqish uchun kerakli jami ball.
# ENG_LEVELS bilan bir tartibda (beginner ... native).
ENG_LEVEL_POINTS = [0, 500, 1400, 3000, 6000, 11000, 20000]

# Bitta KO'NIKMA bo'yicha: yig'ilgan ball -> 0-100 ball.
# Tayanch nuqtalar (oralig'i chiziqli bo'linadi):
#   950  -> 44  = B2 tugadi   -> IELTS 6.0
#   1800 -> 70  = C1 tugadi   -> IELTS 7.5
#   3200 -> 95  = C2          -> IELTS 9.0
# Jahongir: "hozir u B2gacha grammatika ishlagan xolos bu degani
# hozir grammatika IELTS 6.0".
SKILL_SCORE_SCALE = [
    (0, 0), (120, 8), (280, 18), (520, 30), (950, 44),
    (1800, 70), (3200, 95), (4200, 100),
]

# 0-100 ball -> IELTS band.
# Jahongir: "95-100 bu c2 yani IELTS 9.0 BOLSA qolganini 85-95ni
# 8,5ga moslashtir qolganini shunga qarab mos ravishda moslashtirib
# qoyaver" — yuqorida har 10 ball 0.5 band, pastda qadam ixchamroq.
# Tayanch nuqtalar: A1=8 -> 3.0, A2=18 -> 4.0, B1=30 -> 5.0,
# B2=44 -> 6.0, C1=70 -> 7.5, C2=95 -> 9.0
IELTS_BANDS = [
    (95, 9.0), (85, 8.5), (75, 8.0), (65, 7.5), (55, 7.0),
    (48, 6.5), (40, 6.0), (34, 5.5), (28, 5.0), (23, 4.5),
    (18, 4.0), (13, 3.5), (8, 3.0), (3, 2.5), (1, 2.0),
]

# 0-100 ball -> CEFR yorlig'i (yuqoridagi tayanch nuqtalar bilan bir xil)
SCORE_CEFR = [
    (95, "C2"), (70, "C1"), (44, "B2"), (30, "B1"),
    (18, "A2"), (8, "A1"), (0, "-"),
]


def level_index_for(points: float) -> int:
    """Umumiy ball -> ENG_LEVELS indeksi."""
    idx = 0
    for i, need in enumerate(ENG_LEVEL_POINTS):
        if points >= need:
            idx = i
    return min(idx, len(ENG_LEVELS) - 1)


def skill_score(points: float) -> int:
    """Ko'nikma bali (yig'ilgan to'g'ri javoblar) -> 0-100."""
    p = max(0.0, float(points or 0))
    sc = SKILL_SCORE_SCALE
    if p >= sc[-1][0]:
        return 100
    for i in range(len(sc) - 1):
        lo_p, lo_s = sc[i]
        hi_p, hi_s = sc[i + 1]
        if p < hi_p:
            frac = (p - lo_p) / max(1, hi_p - lo_p)
            return int(round(lo_s + frac * (hi_s - lo_s)))
    return 100


# LUG'AT uchun ALOHIDA shkala (2026-09-25). Jahongir: "lugat balli 9.0
# soz kamku u yerda 9.0 uchun 15000+ soz kerak kamida ... umumiy
# 100ta unit bolsin ... shundan kelib chiqib IELTS ball bersin".
# Ilgari lug'at ham umumiy SKILL_SCORE_SCALE bilan yurardi — 3 200 ta
# so'z 9.0 berardi. Endi ball = kamida bir marta to'g'ri topilgan
# ALOHIDA so'zlar soni, tayanch nuqtalar so'z boyligi tadqiqotlari
# bo'yicha (A1 ~300-500, A2 ~1000, B1 ~2000, B2 ~4000, C1 ~7000,
# C2 ~10000 so'z oilasi):
#     300 -> 8  = A1 (3.0)      3500 -> 44 = B2 (6.0)
#     800 -> 18 = A2 (4.0)      6500 -> 70 = C1 (7.5)
#    1800 -> 30 = B1 (5.0)     10000 -> 95 = C2 (9.0)
# 100 unit (1–33 bot + 34–100 chastota) jami ~10 450 so'z — 9.0 uchun
# deyarli hammasini bilish kerak. Raqamlarni o'zgartirish shu yerda.
VOCAB_SCORE_SCALE = [
    (0, 0), (300, 8), (800, 18), (1800, 30), (3500, 44),
    (6500, 70), (10000, 95), (10450, 100),
]


def _interp_score(points: float, scale: list) -> int:
    p = max(0.0, float(points or 0))
    if p >= scale[-1][0]:
        return 100
    for i in range(len(scale) - 1):
        lo_p, lo_s = scale[i]
        hi_p, hi_s = scale[i + 1]
        if p < hi_p:
            frac = (p - lo_p) / max(1, hi_p - lo_p)
            return int(round(lo_s + frac * (hi_s - lo_s)))
    return 100


def vocab_score(words: float) -> int:
    """Lug'at: bilingan so'zlar soni -> 0-100 (VOCAB_SCORE_SCALE)."""
    return _interp_score(words, VOCAB_SCORE_SCALE)


def score_for_skill(skill: str, points: float) -> int:
    """Ko'nikma bo'yicha to'g'ri shkala: lug'at o'ziniki, qolganlari
    umumiy. Hamma joy (o'quvchi kartasi, dashboard, mashq sahifasi)
    shu bitta funksiyadan o'tsin — ikki xil hisob bo'lib ketmasin."""
    if skill == "vocabulary":
        return vocab_score(points)
    return skill_score(points)


def points_for_score(score: float) -> int:
    """skill_score teskarisi: shu 0-100 ballga chiqish uchun necha
    ball kerak."""
    sc = SKILL_SCORE_SCALE
    t = max(0.0, min(100.0, float(score)))
    for i in range(len(sc) - 1):
        lo_p, lo_s = sc[i]
        hi_p, hi_s = sc[i + 1]
        if t <= hi_s:
            frac = (t - lo_s) / max(1, hi_s - lo_s)
            return int(round(lo_p + frac * (hi_p - lo_p)))
    return sc[-1][0]


def score_for_band(band: float) -> int:
    """Shu bandga yetish uchun kerakli eng kichik 0-100 ball."""
    best = 0
    for lo, b in sorted(IELTS_BANDS, key=lambda x: x[0]):
        if b <= band:
            best = lo
    for lo, b in IELTS_BANDS:
        if b >= band:
            best = lo
    return best


def ielts_band(score: float) -> float:
    """0-100 ball -> IELTS band. 0 ball = 0 (hali baholanmagan)."""
    for lo, band in IELTS_BANDS:
        if score >= lo:
            return band
    return 0.0


def score_cefr(score: float) -> str:
    for lo, lbl in SCORE_CEFR:
        if score >= lo:
            return lbl
    return "-"


def ielts_round(value: float) -> float:
    """IELTS yaxlitlash qoidasi: .25 -> .5, .75 -> keyingi butun."""
    whole = int(value)
    rest = value - whole
    if rest < 0.25:
        return float(whole)
    if rest < 0.75:
        return whole + 0.5
    return float(whole + 1)


def ielts_overall(bands: list) -> float:
    """Ko'nikma bandlarining o'rtachasi -> umumiy IELTS bali.

    Jahongir: "endi hamma skillarni qoshib ortachasini chiqarganda
    uni IELTS balli kelib chiqsin"."""
    if not bands:
        return 0.0
    return min(9.0, ielts_round(sum(bands) / len(bands)))

# KO'NIKMALAR (skills). Jony Student ilovasida o'quvchi UMUMIY
# darajasini ko'radi, ustiga bosganda esa har bir ko'nikma bo'yicha
# ALOHIDA darajasi va keyingi darajagacha qancha qolganini ko'radi
# (2026-08-09, Jahongir so'radi). Har bir ko'nikma bir xil zinadan
# (ENG_LEVELS) yuradi, lekin balli alohida yig'iladi.
SKILLS = [
    ("vocabulary", "Lug'at",     "sky"),
    ("grammar",    "Grammatika", "violet"),
    ("reading",    "O'qish",     "emerald"),
    ("listening",  "Tinglash",   "amber"),
    ("writing",    "Yozish",     "rose"),
    ("speaking",   "Gapirish",   "teal"),
]
SKILL_KEYS = [k for k, _, _ in SKILLS]
SKILL_LABELS = {k: lbl for k, lbl, _ in SKILLS}
SKILL_TONE = {k: t for k, _, t in SKILLS}

# Lug'at o'yinlari (Jony Student). Ro'yxatga yangi o'yin qo'shilsa
# frontend avtomat ko'rsatadi — alohida kod yozish shart emas.
# JonyLugatBot'dagi mashq turlari bilan bir xil (bot.py: EX) —
# bola botda ham, ilovada ham AYNAN o'sha o'yinlarni ko'radi.
# Botdagi "🎤 Ovozli javob" hozircha yo'q (mikrofon/nutq tanish
# alohida ish, keyingi bosqichga qoldirildi).
VOCAB_GAMES = [
    ("en_uz",      "Ko'p tanlov (EN→UZ)", "4 ta variantdan to'g'risini tanlang"),
    ("uz_en",      "Ko'p tanlov (UZ→EN)", "4 ta variantdan to'g'risini tanlang"),
    ("spelling",   "Yozib javob berish",  "So'zni inglizcha yozib chiqing"),
    ("truefalse",  "To'g'ri / Xato",      "Tarjima to'g'rimi — hal qiling"),
    ("scramble",   "Harflarni tartiblash", "Aralashgan harflardan so'z yasang"),
    ("flashcard",  "Kartochka",           "O'zingizni o'zingiz tekshiring"),
    ("match",      "Juftlash",            "So'z va tarjimasini juftlang"),
]
VOCAB_GAME_KEYS = [k for k, _, _ in VOCAB_GAMES]
VOCAB_GAME_LABELS = {k: lbl for k, lbl, _ in VOCAB_GAMES}

# Bitta o'yin turida nechta savol bo'ladi va har to'g'ri javob uchun
# necha XP beriladi.
VOCAB_ROUND_SIZE = 10
VOCAB_XP_PER_CORRECT = 1.0

# Grammar mashqlari (2026-08-10): bitta mashg'ulotda nechta savol
# va har birinchi-marta-to'g'ri javob uchun necha XP.
# 2026-08-24, Jahongir: "mashqlar soni 9ta bu juda kam buni sonini
# 20ta kotarish kerak"
GRAMMAR_ROUND_SIZE = 20
GRAMMAR_XP_PER_CORRECT = 1.0

ENG_LEVELS = [
    # "need" — shu darajaga chiqish uchun kerakli JAMI ball
    # (ENG_LEVEL_POINTS bilan bir xil, pastda tekshiriladi).
    {"key": "beginner",          "label": "Beginner",
     "ielts": "~2.0-2.5", "cefr": "A1",     "need": 0},
    {"key": "elementary",        "label": "Elementary",
     "ielts": "~3.0-3.5", "cefr": "A2",     "need": 500},
    {"key": "pre_intermediate",  "label": "Pre-Intermediate",
     "ielts": "~4.0-4.5", "cefr": "B1",     "need": 1400},
    {"key": "intermediate",      "label": "Intermediate",
     "ielts": "~5.0-5.5", "cefr": "B1+/B2", "need": 3000},
    {"key": "upper_intermediate", "label": "Upper-Intermediate",
     "ielts": "~6.0-6.5", "cefr": "B2/C1",  "need": 6000},
    {"key": "advanced",          "label": "Advanced",
     "ielts": "~7.0-8.0", "cefr": "C1",     "need": 11000},
    {"key": "native",            "label": "Native",
     "ielts": "~8.5-9.0", "cefr": "C2",     "need": 20000},
]
assert [x["need"] for x in ENG_LEVELS] == ENG_LEVEL_POINTS


REFUND_REQUEST = [SALES_MANAGER, FOUNDER, PARTNER_HEAD]
REFUND_APPROVE = [BRANCH_MANAGER, FINANCE_DIRECTOR, FOUNDER]
REFUND_VIEW = list(dict.fromkeys(
    REFUND_REQUEST + REFUND_APPROVE + [SALES_HEAD]))
# Sovg'a ro'yxati, coin qoidasi va qo'lda coin berish - faqat rahbariyat.
# NUSXA (list(...)), alias EMAS — 2026-09-06 auditi: entry.py bu
# ro'yxatga HR menejerni qo'shadi; alias bo'lganida HR bilmagan holda
# FULL_ACCESS ga (LC UP pul importi, shtat tasdig'i va h.k.) ega
# bo'lib qolardi. Endi coin huquqi coin bilan cheklanadi.
COIN_ADMIN = list(FULL_ACCESS)

# COIN BALANSINI TO'G'RILASH (qalamcha) — asoschi va FILIAL RAHBARI.
#
# 2026-09-01, Jahongir: "filial rahbarlari balansni tahrirlash huquqi
# bormi yoq bolsa shu tahrirlash huquqi bolsin".
#
# PUL balansi filial rahbariga allaqachon ochiq edi (CASH_ACCESS —
# yozuv qo'shish, PAYMENT_EDIT — summani tahrirlash). Yopiq bo'lgani
# COIN balansi edi: u faqat asoschida turardi. Endi filial rahbari
# ham to'g'rilaydi, lekin FAQAT O'Z FILIALI o'quvchisiga (server
# tekshiradi).
#
# Bu ATAYLAB alohida ro'yxat: COIN_ADMIN = FULL_ACCESS bilan bir xil
# obyekt bo'lgani uchun (entry.py unga HR menejerni qo'shadi), unga
# tayanib qolsak, huquq bilmagan holda HR ga ham o'tib ketardi.
COIN_BALANCE_EDIT = [FOUNDER, BRANCH_MANAGER]
# PUL BALANSINI TO'G'RILASH (2026-09-26, Jahongir: "o'quvchi kartasiga
# balans tahrirlash qo'shib ber faqat filial rahbariga ruxsat
# berilsin"). Faqat filial rahbari va faqat o'z filiali o'quvchisi.
MONEY_BALANCE_EDIT = [BRANCH_MANAGER]
# Tuzatish yozuvining turi: kassaga TUSHUM ham, hisoblangan to'lov ham
# emas — hisobotlar faqat "payment"/"charge"/"discount"ni sanaydi,
# balans esa hamma yozuvlar yig'indisi.
PAYMENT_ADJUST_KIND = "adjustment"

# ---- Adminlar (sotuv menejeri) KPI ------------------------------------
# Admin ish haqi = fiks oylik + eski to'lovlarni yig'ish bonusi +
# yangi mijoz bonusi. Ikkala bonus ham FILIAL ko'rsatkichi bo'yicha
# hisoblanadi: bir filialda ikkita admin bo'lsa, ikkalasi ham to'liq
# bonusni oladi.

# Eski to'lov = ilgari kamida bir marta to'lagan o'quvchining keyingi
# to'lovi. Yangi to'lov = o'quvchining eng birinchi to'lovi.

# Yig'ish foizi SUMMA bo'yicha: shu oyda eski o'quvchilarga hisoblangan
# summadan qanchasi kassaga tushgani.

# (min_students, max_students yoki None, min_percent, bonus)
DEFAULT_KPI_COLLECTION_RULES = [
    (51, 100, 95.0, 500_000),
    (101, 150, 95.0, 1_000_000),
    (101, 150, 90.0, 500_000),
    (151, None, 98.0, 2_000_000),
    (151, None, 90.0, 1_000_000),
    (151, None, 80.0, 500_000),
]
# 50 tagacha o'quvchida bonus yo'q - shuning uchun jadvalda qator ham yo'q.

# (yangi mijozlar soni, bonus)
DEFAULT_KPI_NEW_CLIENT_RULES = [
    (10, 50_000),
    (20, 120_000),
    (30, 300_000),
    (40, 500_000),
    (50, 750_000),
    (60, 1_200_000),
    (70, 1_800_000),
    (80, 2_400_000),
    (90, 3_150_000),
    (100, 4_000_000),
]

# KPI'ni ko'rish - rahbariyat; qoidalar va fiks oylikni o'zgartirish -
# faqat asoschi.
KPI_VIEW = FULL_ACCESS + [FINANCE_DIRECTOR, SALES_HEAD,
                          SALES_MANAGER, ADMINISTRATOR]
KPI_ADMIN = [FOUNDER]

# ---- Fanlar va darajalar ----------------------------------------------
# Guruh ochilganda fan va daraja tanlanadi. Ta'lim sifati hisoboti ham
# shu kesimda chiqadi.

# NOMZOD LAVOZIMLARI (2026-08-15). Ochiq ariza formasi ham,
# nomzodlar ro'yxatidagi filtr ham shu ro'yxatdan oziqlanadi —
# ikki joyda ikki xil bo'lib ketmasin.
APPLY_POSITIONS = [
    ("teacher", "Ustoz"),
    ("support", "Support teacher"),
    ("examiner", "Examiner"),
    ("sales", "Sotuv menejeri"),
    ("cleaner", "Farrosh"),
    ("other", "Boshqa"),
]
APPLY_POSITION_LABELS = dict(APPLY_POSITIONS)

# Sertifikat SHART bo'lgan lavozimlar (ochiq arizada tekshiriladi)
APPLY_CERT_REQUIRED = ("teacher", "examiner", "support")

APPLY_MARITAL = [
    ("single", "Turmush qurmagan"),
    ("married", "Oilali"),
    ("divorced", "Ajrashgan"),
]
APPLY_MARITAL_LABELS = dict(APPLY_MARITAL)

# "Qancha vaqt ishlamoqchisiz?" javoblari
APPLY_WORK_DURATIONS = [
    "3-6 oy",
    "6 oy - 1 yil",
    "1-2 yil",
    "2 yildan ko'p (uzoq muddat)",
]

# O'QUVCHI HOLATLARI (2026-08-15). "left" — guruhdan chiqarilgan,
# lekin hali arxivga tushmagan (odatda qarzi bor).
#
# Jahongir: "birorta oquvchi guruhsiz lekin faol bola olmaydi
# guruhdan chiqarildimi u faol emas endi ... qarzi bolsa
# qarzdorlarda, qarzi yoq bolsa arxivga tushsin".
STUDENT_LEFT = "left"
STUDENT_STATUSES = [
    ("active", "Faol"),
    ("trial", "Sinovda"),
    ("frozen", "Muzlatilgan"),
    ("left", "Chiqib ketgan"),
    ("archived", "Arxiv"),
]
STUDENT_STATUS_LABELS = dict(STUDENT_STATUSES)
# Markazda hisobga olinadigan (arxivga tushmagan) holatlar
STUDENT_OPEN_STATUSES = ["active", "trial", "frozen", "left"]

# JONY STUDENT ILOVASIGA KIRISH HUQUQI (2026-08-25).
# Jahongir: "akkaunti muzlatilsa yoki darsdan chiqib ketsa bu appga
# kirmay qolishi kerak".
# Muzlatilgan, chiqib ketgan va arxivdagilar ilovaga kira olmaydi.
# Tekshiruv HOLAT bo'yicha ishlaydi (hisob o'chirilmaydi) — o'quvchi
# qaytib faollashsa, ilova o'zi ochiladi, qo'lda hech nima qilish
# shart emas va bironta ma'lumot yo'qolmaydi.
STUDENT_APP_STATUSES = ["active", "trial"]
STUDENT_APP_BLOCK_TEXT = {
    "frozen": ("Hisobingiz vaqtincha muzlatilgan. O'qish qayta "
               "boshlanganda ilova o'zi ochiladi."),
    "left": ("Siz guruhdan chiqarilgansiz. Qayta qo'shilganingizda "
             "ilova o'zi ochiladi."),
    "archived": ("Hisobingiz arxivga o'tkazilgan. Savollar bo'lsa "
                 "administratorga murojaat qiling."),
}
STUDENT_APP_BLOCK_DEFAULT = ("Ilova hozircha yopiq. Administratorga "
                             "murojaat qiling.")


def student_app_block_reason(status: str) -> str | None:
    """O'quvchi ilovaga kira oladimi? Kira olmasa — sababi."""
    if (status or "") in STUDENT_APP_STATUSES:
        return None
    return STUDENT_APP_BLOCK_TEXT.get(
        status or "", STUDENT_APP_BLOCK_DEFAULT)

SUBJECTS = [
    ("english", "Ingliz tili"),
    ("russian", "Rus tili"),
    ("korean", "Koreys tili"),
    ("turkish", "Turk tili"),
    ("german", "Nemis tili"),
    ("kids_english", "Kids English"),
    ("biology", "Biologiya"),
    ("programming", "Dasturlash"),
    ("mental_math", "Mental arifmetika"),
    ("robotics", "Robototexnika"),
    # 2026-09-26, Jahongir: "endi matematikanini ozing tuzib qoy" —
    # maktab matematikasi (Boshlang'ich 5–6, O'rta 7–9, Yuqori 10–11)
    ("math", "Matematika"),
]
SUBJECT_LABELS = dict(SUBJECTS)

# Ingliz tilida o'z bosqichlarimiz bor; qolgan tillarda xalqaro
# CEFR shkalasi (A1-B2) ishlatiladi.
CEFR_LEVELS = [
    ("a1", "A1"),
    ("a2", "A2"),
    ("b1", "B1"),
    ("b2", "B2"),
]

ENGLISH_LEVELS = [
    ("step1", "Step 1"),
    ("step2", "Step 2"),
    ("step3", "Step 3"),
    ("step4", "Step 4"),
    ("ielts_intro", "IELTS Introduction"),
    ("ielts_foundation", "IELTS Foundation"),
    ("ielts_graduation", "IELTS Graduation"),
    ("cefr", "CEFR"),
]

# Til bo'lmagan fanlar (masalan biologiya) uchun oddiy bosqichlar
COURSE_LEVELS = [
    ("basic", "Boshlang'ich"),
    ("intermediate", "O'rta"),
    ("advanced", "Yuqori"),
]

# Kids English — Cambridge YLE bosqichlari
KIDS_LEVELS = [
    ("starters", "Starters"),
    ("movers", "Movers"),
    ("flyers", "Flyers"),
]

SUBJECT_LEVELS = {
    "english": ENGLISH_LEVELS,
    "russian": CEFR_LEVELS,
    "korean": CEFR_LEVELS,
    "turkish": CEFR_LEVELS,
    "german": CEFR_LEVELS,
    "kids_english": KIDS_LEVELS,
    "biology": COURSE_LEVELS,
    "programming": COURSE_LEVELS,
    "mental_math": COURSE_LEVELS,
    "robotics": COURSE_LEVELS,
    "math": COURSE_LEVELS,
}

# Barcha daraja kalitlari - tekshirish uchun
ALL_LEVELS = {k for levels in SUBJECT_LEVELS.values() for k, _ in levels}
LEVEL_LABELS = {k: lbl for levels in SUBJECT_LEVELS.values() for k, lbl in levels}


def level_valid(subject: str, level: str) -> bool:
    """Daraja tanlangan fanga tegishlimi. Masalan rus tilida "Step 1"
    bo'lishi mumkin emas."""
    if not level:
        return True
    return level in {k for k, _ in SUBJECT_LEVELS.get(subject, [])}


# ---- Dars kunlari -----------------------------------------------------
WEEKDAYS = [
    ("mon", "Dushanba", "Du"),
    ("tue", "Seshanba", "Se"),
    ("wed", "Chorshanba", "Ch"),
    ("thu", "Payshanba", "Pa"),
    ("fri", "Juma", "Ju"),
    ("sat", "Shanba", "Sha"),
    ("sun", "Yakshanba", "Ya"),
]
WEEKDAY_KEYS = [k for k, _, _ in WEEKDAYS]
WEEKDAY_LABELS = {k: lbl for k, lbl, _ in WEEKDAYS}


# =====================================================================
#  Avtomatik tekshiruvlar (guardrails)
#  Xato odam qilmaydi - tizim yo'l qo'ymaydi. Har bir tekshiruv "block"
#  (mumkin emas) yoki "warn" (mumkin, lekin ogohlantiriladi) bo'ladi.
# =====================================================================

# Bitta ustoz kuniga eng ko'pi bilan nechta dars bera oladi va haftasiga
# nechta guruh olib bora oladi. Bundan oshsa sifat tushadi.
TEACHER_MAX_LESSONS_PER_DAY = 4
TEACHER_MAX_GROUPS = 8
# Support uchun norma (2026-08-12): bitta support nechta
# guruhgacha biriktirilishi me'yoriy hisoblanadi.
SUPPORT_MAX_GROUPS = 4

# Darslar orasidagi mantiqsiz bo'shliq. Ustoz 09:00 da dars berib,
# keyingisi 19:00 da bo'lsa - kuni behuda ketadi.
MAX_GAP_HOURS = 5

CHECKS = [
    # 2026-09-30: arxivdagi guruhga o'quvchi qo'shilmaydi
    ("group_archived", "Guruh arxivda", "block"),
    ("teacher_clash", "Ustoz bir vaqtda ikki guruhda", "block"),
    ("age_limit", "Kurs yosh chegarasiga mos emas", "block"),
    ("age_unknown", "Tug'ilgan sana kiritilmagan", "warn"),
    ("room_clash", "Xona bir vaqtda ikki guruhda", "block"),
    ("over_capacity", "Sig'imdan ortiq o'quvchi", "block"),
    ("teacher_overload", "Ustozning maksimal yuklamasidan oshish", "block"),
    ("bad_gap", "Darslar orasida mantiqsiz bo'shliq", "warn"),
    ("level_mismatch", "O'quvchi darajasiga mos bo'lmagan guruh", "warn"),
]
CHECK_LABELS = {k: lbl for k, lbl, _ in CHECKS}
CHECK_SEVERITY = {k: sev for k, _, sev in CHECKS}

# Kurs bo'yicha yosh chegarasi: (min_yosh, max_yosh). Kids English —
# faqat 7-12 yoshdagi bolalar.
SUBJECT_AGE_LIMITS = {
    "kids_english": (7, 12),
}


def time_to_minutes(t: str) -> int | None:
    """"09:00" -> 540. Noto'g'ri format bo'lsa None."""
    try:
        h, m = (t or "").strip().split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def ranges_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """Ikki dars vaqti kesishadimi. Chegara tegib turishi (11:00 tugab
    11:00 boshlanishi) kesishish emas."""
    a0, a1 = time_to_minutes(a_start), time_to_minutes(a_end)
    b0, b1 = time_to_minutes(b_start), time_to_minutes(b_end)
    if None in (a0, a1, b0, b1):
        return False
    return a0 < b1 and b0 < a1


# =====================================================================
#  Chegirmalar
#  Chegirma - pul. Shuning uchun uni xodim o'zboshimchalik bilan bera
#  olmaydi: har birida sabab, miqdor, muddat va TASDIQLAGAN SHAXS bo'ladi.
# =====================================================================

DISCOUNT_TYPES = [
    ("family", "Oila chegirmasi", "Bir oiladan ikki va undan ortiq farzand"),
    ("referral", "Referral", "Do'sti olib kelgan - qaysi do'sti belgilanadi"),
    ("staff_child", "Xodim farzandi", "Xodim ketsa chegirma avtomat bekor bo'ladi"),
    ("grant", "Grant", "Bilimi yoki natijasi uchun"),
    ("promo", "Aksiya", "Vaqtinchalik marketing aksiyasi"),
    ("social", "Ijtimoiy yordam", "Oilaviy og'ir sharoit"),
    ("individual", "Individual ruxsat", "Asoschi shaxsan ruxsat bergan"),
    ("coin_shop", "Jony Shop (coinga)",
     "O'quvchi o'z coinига do'kondan sotib olgan"),
    ("app_referral", "Do'st taklifi (avtomat)",
     "Havola orqali kelgan do'sti to'lov qilgani uchun - tizim o'zi qo'yadi"),
    ("wheel", "Baraban sovg'asi (avtomat)",
     "Lid testi oxirida barabandan tushgan - faqat BIRINCHI oyga, "
     "tizim o'zi qo'yadi"),
]
DISCOUNT_TYPE_LABELS = {k: lbl for k, lbl, _ in DISCOUNT_TYPES}
DISCOUNT_TYPE_HINTS = {k: h for k, _, h in DISCOUNT_TYPES}

# Qaysi chegirmani tizim o'zi boshqaradi - qo'lda tegilmaydi.
AUTO_DISCOUNT_TYPES = ["family", "coin_shop", "app_referral", "wheel"]

# ======================================================================
#  BARABAN (2026-09-25, Jahongir: "barabanda xar xil sovgalar
#  skidkalar 10-100%gacha coinlar 10-100gacha bo'lishi kerak")
# ======================================================================
#
#  Standart bo'laklar va EHTIMOLLIKLARI (og'irlik = foiz). Bu faqat
#  BOSHLANG'ICH ro'yxat — bazaga bir marta yoziladi, keyin asoschi
#  Sozlamalardan o'zgartiradi. Kod ustunlik qilmaydi.
#
#  O'rtacha xarajat: har aylantirishga birinchi oy to'lovining ~13%
#  (0.2·10 + 0.12·20 + 0.08·30 + 0.06·50 + 0.03·70 + 0.01·100).
#  100 liddan 1 tasi birinchi oy bepul o'qiydi.
WHEEL_DEFAULT_PRIZES = [
    # (tur, qiymat, og'irlik, yorliq)
    ("coin",     10, 20.0, "10 tanga"),
    ("coin",     30, 15.0, "30 tanga"),
    ("coin",     50, 10.0, "50 tanga"),
    ("coin",    100,  5.0, "100 tanga"),
    ("discount", 10, 20.0, "10% chegirma"),
    ("discount", 20, 12.0, "20% chegirma"),
    ("discount", 30,  8.0, "30% chegirma"),
    ("discount", 50,  6.0, "50% chegirma"),
    ("discount", 70,  3.0, "70% chegirma"),
    ("discount", 100, 1.0, "100% chegirma"),
]
# Shu foizdan boshlab asoschiga darrov Telegram xabar boradi
# (Jahongir tasdiqladi: avtomat qo'llanadi, lekin u bilib turadi).
WHEEL_NOTIFY_FROM_PERCENT = 70
# SO'M CHEGIRMA (2026-09-26, Jahongir: "skidka ham foizli ham summali
# bo'lsin"). Baraban bo'lagi "discount_sum" — qiymat so'mda, birinchi
# oy to'lovidan ayiriladi. Shu summadan boshlab asoschiga xabar.
WHEEL_NOTIFY_FROM_SUM = 300_000
WHEEL_SUM_MIN = 1_000
WHEEL_SUM_MAX = 5_000_000
WHEEL_DISCOUNT_KINDS = ("discount", "discount_sum")


def som_short(v) -> str:
    """50000 -> "50 000 so'm" (baraban yorlig'i uchun)."""
    return f"{int(v):,}".replace(",", " ") + " so'm"
# Baraban chegirmasi qancha oyga: faqat BIRINCHI oy (Jahongir
# tasdiqladi — aks holda 100% tushgan bola butun kurs bepul o'qirdi).
WHEEL_DISCOUNT_MONTHS = 1

# ======================================================================
#  REFERAL DASTURI  (2026-08-28, Jahongir)
# ======================================================================
#
#  Jahongirning so'zi bilan:
#    "o'quvchiga maxsus link beriladi ... u o'quvchi ro'yxatdan o'tadi
#     va adminlarga so'rov boradi yangi lid bo'lib, lidni obrabotka
#     qilib guruhga qo'yib to'lov qilgandan keyin 10% chegirma oladi,
#     2-do'sti uchun esa 30%, 3-do'sti uchun esa 50% ... 4-do'sti
#     uchun 75%, 5-do'sti uchun 100%"
#    "yani bitta olib kelsa shu 10% bo'ladi 2-do'stiga esa 30% bo'ladi
#     QO'SHILMAYDI 10+30=40% bo'lmaydi"
#    "faqat 1 oy bepul, to'laganlargina hisobga olinadi, 2 oy emas SHU
#     OY ichida qilaylik"
#    "oilaviy chegirmasi bo'lsa o'sha to'laydigan summadan 10% foiz
#     hisoblanib ketaveradi"
#
#  Uchta qoida shu yerda, bitta joyda turadi - kod bo'ylab tarqalib
#  ketmasin:
#
#  1) PILLAPOYA QO'SHILMAYDI. Daraja oldingisini ALMASHTIRADI.
#     2 ta do'st = 30% (10+30=40 EMAS).
REFERRAL_LADDER = {1: 10.0, 2: 30.0, 3: 50.0, 4: 75.0, 5: 100.0}
REFERRAL_MAX_LEVEL = 5

#  2) OYNA - BIR OY. Do'st SHU OY ichida to'lasa hisobga olinadi.
#     Keyingi oy hisob noldan boshlanadi.
REFERRAL_WINDOW = "month"

#  3) MUKOFOT - BIR OYGA. Chegirma bitta oyga beriladi, keyin tugaydi.
REFERRAL_REWARD_MONTHS = 1

#  4) BOSHQA CHEGIRMA BILAN QANDAY QO'SHILADI. Foiz oylik narxdan
#     emas, o'quvchi HAQIQATDA TO'LAYDIGAN summadan olinadi. Ya'ni
#     oilaviy 20% bo'lsa: 500 000 -> 400 000 -> referal 10% -> 40 000
#     chegirma -> 360 000 to'laydi. Jami 28%, 30% emas.
REFERRAL_ON_PAYABLE = True

# Do'st qaysi bosqichda ekani (o'quvchiga ko'rinadigan matn).
REFERRAL_STAGE_LABELS = {
    "invited": "Ro'yxatdan o'tdi",
    "processing": "Admin bog'lanmoqda",
    "enrolled": "Guruhga qo'shildi",
    "paid": "To'lov qildi - hisobga olindi",
    "expired": "Muddati o'tdi (boshqa oyda)",
}

def referral_percent(n_paid: int) -> float:
    """Shu oyda TO'LAGAN do'stlar soniga qarab foiz.

    Qo'shilmaydi: 3 ta do'st = 50%, (10+30+50)=90% EMAS."""
    if n_paid <= 0:
        return 0.0
    return REFERRAL_LADDER[min(int(n_paid), REFERRAL_MAX_LEVEL)]


def referral_next_hint(n_paid: int) -> str:
    """Keyingi darajagacha nima qilish kerakligi - ilovada ko'rinadi."""
    if n_paid >= REFERRAL_MAX_LEVEL:
        return "Eng yuqori daraja - bu oy to'liq bepul!"
    nxt = int(n_paid) + 1
    return (f"Yana 1 ta do'st to'lov qilsa - {REFERRAL_LADDER[nxt]:.0f}% "
            f"chegirma ({nxt}-do'st)")

# DO'KON CHEGIRMASI QAYSI OYGA TUSHADI.
#
# ESKI qoida (2026-08-15): 15-kungacha shu oyga, keyin keyingi oyga.
# YANGI qoida (2026-08-20, Jahongir: "bunda coin yechildi lekin
# avtomat skidka bermadi balansini deyabdi ... osha olgan oyiga
# tolamagan bolsa shu olgan oyiga balans ozgarsin, agar tolagan
# bolsa keyingi oyga"): sanaga emas, BALANSGA qaraladi -
#   qarzi bor (balans < 0)  -> shu oyga, darrov tushadi;
#   to'lab bo'lgan          -> keyingi oyga.
SHOP_DISCOUNT_CUTOFF_DAY = 15  # eski qoida; endi ishlatilmaydi

# QAYSI CHEGIRMA AVTOMAT BERILADI (2026-08-20, Jahongir: "33% lik va
# 100% lik chegirmalarni o'quvchi shopdan sotib olganda coini yetsa
# avtomat berilsin admin tasdiqlashi shartmas, qolganlarini admin
# tasdiqlashi va berishi kerak bo'ladi").
#
# Bu ikkisi bizning standart, hamma biladigan chegirmalarimiz -
# ularni tasdiqlatib o'tirish ortiqcha ish. Boshqa har qanday
# chegirma (masalan bir martalik aksiya foizi) va barcha qo'lga
# beriladigan sovg'alar avvalgidek xodim tasdig'idan o'tadi.
AUTO_SHOP_DISCOUNT_PERCENTS = [33.0, 100.0]


def shop_auto_discount(reward) -> bool:
    """Shu do'kon mahsuloti avtomat beriladimi?

    Faqat chegirma turidagi va foizi ruxsat etilgan ro'yxatda
    bo'lganlar. Qat'iy so'mdagi chegirma (discount_amount) avtomat
    bo'lmaydi - uni ham xodim ko'rib chiqadi."""
    if (getattr(reward, "kind", "gift") or "gift") != "discount":
        return False
    try:
        pct = round(float(getattr(reward, "discount_percent", 0) or 0), 2)
    except (TypeError, ValueError):
        return False
    return pct in AUTO_SHOP_DISCOUNT_PERCENTS


def shop_discount_period(on=None) -> str:
    """ESKI 15-kun qoidasi — faqat tarix uchun qoldi, yangi kod
    shop_discount_period_by_balance() ishlatadi."""
    d = on or local_today()
    if d.day <= SHOP_DISCOUNT_CUTOFF_DAY:
        return f"{d.year:04d}-{d.month:02d}"
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return f"{y:04d}-{m:02d}"


def shop_discount_period_by_balance(balance: float, on=None) -> str:
    """Chegirma QAYSI OYGA tegishli — o'quvchining pul balansiga qarab
    (2026-08-20, Jahongir): shu oyga to'lamagan (qarzli) bo'lsa shu
    oyga va balans darrov o'zgaradi; to'lab bo'lgan bo'lsa keyingi
    oyga."""
    d = on or local_today()
    if (balance or 0) < 0:
        return f"{d.year:04d}-{d.month:02d}"
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return f"{y:04d}-{m:02d}"

# Chegirmani kim tasdiqlay oladi. Administrator so'rov yubora oladi,
# lekin tasdiqlash asoschi va filial rahbarida.
DISCOUNT_REQUEST = FULL_ACCESS + [SALES_HEAD, SALES_MANAGER,
                                  ADMINISTRATOR, FINANCE_DIRECTOR]
DISCOUNT_APPROVE = [FOUNDER, BRANCH_MANAGER, FINANCE_DIRECTOR]

# Tasdiqsiz chegirma amal qilmaydi.
DISCOUNT_STATUSES = [
    ("pending", "Tasdiq kutilmoqda"),
    ("active", "Amalda"),
    ("expired", "Muddati tugagan"),
    # 2026-08-22, Jahongir: o'quvchi muzlatilsa chegirma ishlamasin,
    # lekin qaytib kelsa o'zi tiklansin — shuning uchun "bekor" emas,
    # VAQTINCHA to'xtatilgan holat.
    ("paused", "Vaqtincha to'xtatilgan"),
    ("cancelled", "Bekor qilingan"),
    ("rejected", "Rad etilgan"),
]
DISCOUNT_STATUS_LABELS = dict(DISCOUNT_STATUSES)

# Bitta o'quvchida jami chegirma shundan oshmasin - aks holda o'qish
# tekinga aylanadi.
MAX_TOTAL_DISCOUNT_PERCENT = 50.0
# 2026-08-12, Jahongir: "100% chegirma qo'ya olmayapman" - ODDIY
# xodimlar uchun chegara 50% ligicha qoladi, lekin ASOSCHI ba'zi
# holatlarda (yetim, alohida kelishuv...) 100% gacha qo'ya oladi.
DISCOUNT_ABSOLUTE_CAP = 100.0


# =====================================================================
#  HR: nomzod kartasi, onboarding, xodim kartasi
# =====================================================================

LANGUAGE_LEVELS = [
    ("none", "Yo'q"),
    ("a1", "A1"), ("a2", "A2"), ("b1", "B1"),
    ("b2", "B2"), ("c1", "C1"), ("c2", "C2"),
    ("ielts5", "IELTS 5.0-5.5"),
    ("ielts6", "IELTS 6.0-6.5"),
    ("ielts7", "IELTS 7.0+"),
]
LANGUAGE_LEVEL_LABELS = dict(LANGUAGE_LEVELS)

# Yakuniy qaror - nomzod kartasining eng pastki qatori.
HIRE_DECISIONS = [
    ("pending", "Qaror qabul qilinmagan"),
    ("hire", "Ishga olinsin"),
    ("reserve", "Zaxiraga"),
    ("reject", "Rad etilsin"),
]
HIRE_DECISION_LABELS = dict(HIRE_DECISIONS)

# Yangi xodim uchun checklist. Birortasi bajarilmasa xodim ishga
# to'liq kirishgan hisoblanmaydi.
ONBOARDING_STEPS = [
    ("docs", "Hujjatlar topshirildi"),
    ("contract", "Shartnoma imzolandi"),
    ("job_desc", "Lavozim yo'riqnomasi berildi"),
    ("account", "Platformaga profil ochildi"),
    ("branch_tour", "Filial bilan tanishtirildi"),
    ("mentor", "Mentor biriktirildi"),
    ("probation_goals", "Sinov muddati maqsadlari belgilandi"),
    ("rules", "Ichki qoidalar o'rganildi"),
    ("training", "Treningdan o'tdi"),
    ("first_review", "Birinchi baholash o'tkazildi"),
]
ONBOARDING_STEP_LABELS = dict(ONBOARDING_STEPS)
ONBOARDING_KEYS = [k for k, _ in ONBOARDING_STEPS]

# Xodim kartasidagi voqealar tarixi. Hammasi bir jadvalda - shunda
# kartani ochganda butun tarix bir joyda ko'rinadi.
STAFF_EVENTS = [
    ("vacation", "Ta'til", "neutral"),
    ("absence", "Kelmadi", "bad"),
    ("late", "Kechikish", "bad"),
    ("training", "Trening", "good"),
    ("review", "Baholash", "neutral"),
    ("discipline", "Intizomiy holat", "bad"),
    ("reward", "Rag'batlantirish", "good"),
    ("bonus", "Bonus", "good"),
    ("note", "Izoh", "neutral"),
]
STAFF_EVENT_LABELS = {k: lbl for k, lbl, _ in STAFF_EVENTS}
STAFF_EVENT_TONE = {k: t for k, _, t in STAFF_EVENTS}


# =====================================================================
#  Filial reytingi
#  Filialni faqat tushum bilan baholash - eng katta xato. Ko'p pul
#  yig'ib, o'quvchini yo'qotayotgan filial "yaxshi" ko'rinib qoladi.
# =====================================================================

BRANCH_RATING_WEIGHTS = [
    ("finance", "Moliyaviy natija", 25),
    ("retention", "O'quvchi saqlanishi", 20),
    ("sales", "Sotuv", 15),
    ("academic", "Akademik natija", 15),
    ("debt", "Qarzdorlik", 10),
    ("parents", "Ota-onalar mamnunligi", 10),
    ("discipline", "Operatsion intizom", 5),
]
BRANCH_RATING_LABELS = {k: lbl for k, lbl, _ in BRANCH_RATING_WEIGHTS}
BRANCH_RATING_DEFAULT = {k: w for k, _, w in BRANCH_RATING_WEIGHTS}

BRANCH_GRADES = [
    (85, "a", "A - namuna"),
    (70, "b", "B - barqaror"),
    (55, "c", "C - e'tibor kerak"),
    (0, "d", "D - aralashuv kerak"),
]


def branch_grade(score: float) -> tuple:
    for limit, key, label in BRANCH_GRADES:
        if score >= limit:
            return key, label
    return "d", "D - aralashuv kerak"


# =====================================================================
#  Vazifalar (ichki nazorat)
#  Majlisdagi qaror vazifaga aylanmasa, majlis choy ichishga aylanadi.
# =====================================================================

TASK_STATUSES = [
    ("new", "Yangi", "slate"),
    ("in_progress", "Jarayonda", "sky"),
    ("review", "Tekshiruvda", "violet"),
    ("done", "Bajarildi", "emerald"),
    ("rework", "Qayta ishlashga", "amber"),
    ("cancelled", "Bekor qilindi", "slate"),
    ("late", "Kechikdi", "red"),
]
TASK_STATUS_LABELS = {k: lbl for k, lbl, _ in TASK_STATUSES}
TASK_STATUS_TONE = {k: t for k, _, t in TASK_STATUSES}
# Yopilgan deb hisoblanadigan statuslar - kechikish shularga tegmaydi.
TASK_CLOSED = ["done", "cancelled"]

TASK_PRIORITIES = [
    ("low", "Past", 1),
    ("normal", "O'rta", 2),
    ("high", "Yuqori", 3),
    ("urgent", "Shoshilinch", 4),
]
TASK_PRIORITY_LABELS = {k: lbl for k, lbl, _ in TASK_PRIORITIES}
TASK_PRIORITY_RANK = {k: r for k, _, r in TASK_PRIORITIES}

TASK_SOURCES = [
    ("manual", "Qo'lda qo'yilgan"),
    ("meeting", "Majlis qarori"),
    ("risk", "Akademik risk"),
    ("complaint", "Shikoyat"),
    ("stock", "Ombor - xarid so'rovi"),
]
TASK_SOURCE_LABELS = dict(TASK_SOURCES)

TASK_ACCESS = [r for r in STAFF_ROLES]   # har bir xodimning vazifasi bor
TASK_MANAGE = FULL_ACCESS + [HR_MANAGER, ACADEMIC_HEAD, SALES_HEAD,
                             HEAD_EXAMINER, HEAD_SUPPORT]


# =====================================================================
#  Ombor va aktivlar
# =====================================================================

ASSET_TYPES = [
    ("computer", "Kompyuter"),
    ("laptop", "Noutbuk"),
    ("tv", "Televizor"),
    ("projector", "Proyektor"),
    ("printer", "Printer"),
    ("furniture", "Stol-stul"),
    ("camera", "Kamera"),
    ("phone", "Telefon"),
    ("ac", "Konditsioner"),
    ("router", "Router"),
    ("other", "Boshqa"),
]
ASSET_TYPE_LABELS = dict(ASSET_TYPES)

ASSET_CONDITIONS = [
    ("new", "Yangi", "emerald"),
    ("good", "Yaxshi", "emerald"),
    ("worn", "Eskirgan", "amber"),
    ("repair", "Ta'mirda", "amber"),
    ("broken", "Buzilgan", "red"),
    ("written_off", "Hisobdan chiqarilgan", "slate"),
]
ASSET_CONDITION_LABELS = {k: lbl for k, lbl, _ in ASSET_CONDITIONS}
ASSET_CONDITION_TONE = {k: t for k, _, t in ASSET_CONDITIONS}

CONSUMABLE_TYPES = [
    ("book", "Kitob", "dona"),
    ("notebook", "Daftar", "dona"),
    ("marker", "Marker", "dona"),
    ("paper", "Qog'oz", "pachka"),
    ("pen", "Ruchka", "dona"),
    ("ink", "Siyoh", "dona"),
    ("welcome_pack", "Welcome pack", "dona"),
    ("certificate", "Sertifikat qog'ozi", "dona"),
    ("other", "Boshqa", "dona"),
]
CONSUMABLE_TYPE_LABELS = {k: lbl for k, lbl, _ in CONSUMABLE_TYPES}
CONSUMABLE_UNITS = {k: u for k, _, u in CONSUMABLE_TYPES}

STOCK_MOVE_REASONS = [
    ("in", "Kirim — keldi"),
    ("out", "Chiqim — berildi / ishlatildi"),
    ("write_off", "Hisobdan chiqarish — yo'qoldi / yaroqsiz"),
    ("correction", "Sanoq tuzatishi"),
]
STOCK_MOVE_LABELS = dict(STOCK_MOVE_REASONS)

INVENTORY_ACCESS = FULL_ACCESS + [HR_MANAGER, FACILITY_MANAGER]
INVENTORY_VIEW = INVENTORY_ACCESS + [ACADEMIC_HEAD, SUPPORT_TEACHER,
                                     ACCOUNTANT]


# =====================================================================
#  Ustoz ish haqi
# =====================================================================
TEACHER_PAYMENT_KINDS = [
    ("advance", "Avans", "Oy o'rtasida berilgan pul"),
    ("salary", "Oylik", "Oylik hisob-kitobi"),
    ("correction", "Tuzatish", "Kam yoki ko'p berilganini to'g'rilash"),
]
TEACHER_PAYMENT_LABELS = {k: lbl for k, lbl, _ in TEACHER_PAYMENT_KINDS}

# Avans - ishlab topilgan puldan ortiq berilmaydi. Bu qoidani hech kim
# aylanib o'tolmaydi: aks holda ustoz ketib qolsa pul qaytmaydi.
ADVANCE_LIMIT_OF_EARNED = 1.0

# Administrator ham oylik beradi (2026-09-16, Jahongir: "administratorga
# oylik berish huquqini ber") — faqat O'Z filiali ustoz/xodimlariga
# (common._check_pay_scope). Hamma oyliklar ro'yxatini ko'rish
# (PAYROLL_VIEW) unga ochilmaydi.
# SALES_MANAGER = hozirgi "Administrator" (2026-09-03 da hamma
# administratorlar shu rolga birlashtirilgan). 2026-09-16 dagi "admin
# oylik bersin" huquqi eski ADMINISTRATOR ga qo'shilib qolgan edi —
# haqiqiy administratorlar bera olmasdi (2026-10-02 tuzatildi). Filial
# chegarasini _check_pay_scope tekshiradi.
SALARY_PAY = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT, ADMINISTRATOR,
                            SALES_MANAGER]
# Berilgan oylikni O'CHIRISH / filialini tuzatish — faqat rahbariyat
# (2026-10-02, Jahongir: administrator "faqat bera olsin").
SALARY_FIX = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT]
# O'zining oyligini har bir ustoz ko'radi
SALARY_SELF_VIEW = STAFF_ROLES


# =====================================================================
#  Qarzdorlar bilan ishlash
# =====================================================================
DEBTOR_ACCESS = FULL_ACCESS + [SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
                               FINANCE_DIRECTOR, ACCOUNTANT]

DEBT_CONTACT_RESULTS = [
    ("promised", "To'lashga va'da berdi", "emerald"),
    ("no_answer", "Javob bermadi", "slate"),
    ("refused", "To'lay olmasligini aytdi", "red"),
    ("paid", "To'lab yubordi", "emerald"),
]
DEBT_CONTACT_LABELS = {k: lbl for k, lbl, _ in DEBT_CONTACT_RESULTS}
DEBT_CONTACT_TONE = {k: t for k, _, t in DEBT_CONTACT_RESULTS}

# Qarzdorni qanchalik tez ushlash kerak
DEBT_URGENCY = [
    (7, "fresh", "Yangi qarz", "slate"),
    (14, "watch", "E'tibor kerak", "amber"),
    (30, "hot", "Kechikkan", "orange"),
    (0, "critical", "Kritik", "red"),
]


def debt_urgency(days: int) -> tuple:
    """Qarz necha kundan beri turibdi - shunga qarab shoshilinchligi."""
    for limit, key, label, tone in DEBT_URGENCY:
        if limit and days <= limit:
            return key, label, tone
    return "critical", "Kritik", "red"


# =====================================================================
#  SMM avtomat vazifalari
#  Yangi xodim kelsa yoki o'quvchi natija qilsa - SMM eslab qolishi
#  shart emas, vazifa o'zi paydo bo'ladi.
# =====================================================================
SMM_AUTO_TASKS = [
    ("new_staff", "Yangi xodimni suratga va videoga olish", 7),
    ("achievement", "O'quvchi natijasi haqida video olish", 5),
]
SMM_TASK_DEADLINE_DAYS = {k: d for k, _, d in SMM_AUTO_TASKS}


# =====================================================================
#  USTOZ DARAJALARI VA KARYERA XARITASI
#
#  Bu jadval - butun tizimning o'zagi: ustozning bir o'quvchidan
#  qancha olishi, nechta guruh olib bora olishi, keyingi darajaga
#  o'tish sharti va qaysi natijada pastga tushishi shu yerdan chiqadi.
#
#  Bu yerdagi raqamlar faqat BOSHLANG'ICH holat: bir marta bazaga
#  tushadi, keyin asoschi UI'dan o'zgartiradi va bu ro'yxat ularga
#  tegmaydi.
# =====================================================================
# key, nom, bir o'quvchidan (so'm), min tajriba (oy), min guruh,
# max guruh, sertifikat nomi, sertifikat balli, keyingi darajaga
# o'tish uchun necha foiz o'quvchi o'tishi kerak, oylik test
# o'rtachasi shundan past bo'lsa tushiriladi, qaysi darajaga
TEACHER_GRADES = [
    ("junior", "Junior teacher", 80000,  5,  1, 1, "CEFR B2",   55.0, 75.0, None, None),
    ("middle", "Middle teacher", 100000, 12, 2, 3, "CEFR B2",   55.0, 70.0, 55.0, "junior"),
    ("senior", "Senior teacher", 120000, 18, 4, 5, "IELTS 6.0+", 6.0, 60.0, 55.0, "middle"),
    ("expert", "Expert teacher", 140000, 24, 6, 7, "IELTS 6.5+", 6.5, 60.0, 60.0, "senior"),
    # Head teacher uchun hujjatda tushirish chegarasi va guruh soni
    # yozilmagan - Expert bilan bir xil qilib qo'yildi.
    ("head",   "Head teacher",   160000, 24, 6, 8, "IELTS 7.0+", 7.0, None, 60.0, "expert"),
    # Metodist: hujjatda talablari bor, lekin BIR O'QUVCHIDAN QANCHA
    # olishi yozilmagan - vaqtincha Head bilan bir xil qo'yildi.
    # Asoschi Karyera bo'limidan haqiqiy raqamni qo'yadi.
    ("metodist", "Metodist teacher", 160000, 36, 6, 8, "IELTS 8.0+", 8.0,
     None, 60.0, "head"),
]
GRADE_ORDER = [g[0] for g in TEACHER_GRADES]
GRADE_LABELS = {g[0]: g[1] for g in TEACHER_GRADES}
FIRST_GRADE = GRADE_ORDER[0]
GRADE_TONES = {"junior": "slate", "middle": "sky", "senior": "teal",
               "expert": "violet", "head": "amber", "metodist": "rose"}

# Hujjatda ochiq aytilgan: "BU TALABLAR VA BOSHQA NARSALAR VAZIYATGA
# VA TALABGA QARAB OZROQ O'ZGARIB TURISHI HAM MUMKIN". Shuning uchun
# yuqoridagi jadval koddan emas, bazadan o'qiladi va UI'dan
# tahrirlanadi - kod faqat birinchi marta to'ldirib beradi.


def next_grade(key: str) -> str | None:
    """Keyingi daraja. Eng yuqorisida bo'lsa - None."""
    if key not in GRADE_ORDER:
        return GRADE_ORDER[0]
    i = GRADE_ORDER.index(key)
    return GRADE_ORDER[i + 1] if i + 1 < len(GRADE_ORDER) else None


# Ustozlikni boshlash sharti: bularsiz guruh ochilmaydi.
TEACHER_ENTRY = [
    ("cert", "IELTS 6.0 yoki CEFR B2 (55 dan yuqori)"),
    ("age", "Yoshi 18+"),
    ("support", "3 oy support teacher lavozimida ishlash tajribasi"),
    ("skill", "Dars berish mahorati mezonidan 50+ ball"),
]
TEACHER_MIN_AGE = 18
TEACHER_MIN_SUPPORT_MONTHS = 3
TEACHER_MIN_SKILL = 50.0

# Head teacher alohida talablar bilan qo'yiladi.
HEAD_MIN_AGE = 22
HEAD_MIN_SKILL = 70.0
HEAD_MIN_RESULTS = 10          # 10 ta IELTS 6.0+ yoki Multilevel B2 natija
HEAD_RESULT_BAND = 6.0

# Metodist: eng yuqori daraja. Head'dan farqi - qo'shimcha xalqaro
# metodika sertifikati va yuqoriroq natija talab qilinadi.
METODIST_MIN_RESULTS = 10      # 10 ta IELTS 7.0+ natija
METODIST_RESULT_BAND = 7.0
METODIST_QUALIFICATIONS = ["CELTA", "TESOL", "DELTA"]
# Qaysi darajaga o'tishda metodika sertifikati talab qilinadi
QUALIFICATION_REQUIRED_FOR = ["metodist"]

# Natija 50% dan past bo'lsa: o'tganlar boshqa ustozga beriladi,
# o'ta olmaganlarini ustozning o'zi tayyorlaydi va bir oydan keyin
# qayta test topshiradi. Shu vaqt ichida unga YANGI GURUH OCHILMAYDI.
REMEDIATION_BELOW = 50.0
REMEDIATION_DAYS = 30

# Avtomat qaror uchun eng kam ma'lumot. Ikkita o'quvchining bitta
# testiga qarab ustozni tushirib yuborish - natija emas, shovqin.
GRADE_MIN_RESULTS = 8          # kamida shuncha natija bo'lsin
GRADE_MIN_EXAMS = 2            # kamida shuncha test o'tkazilgan bo'lsin

# O'quvchi "bosqichdan o'tdi" deb hisoblanishi uchun kerakli foiz.
# Hujjatda alohida aytilmagan - shu qiymatdan boshlanadi va Karyera
# bo'limidan o'zgartiriladi.
LEVEL_PASS_PERCENT = 60.0

# =====================================================================
#  IMTIHON O'TISH BALLI — TEST TURI BO'YICHA (2026-09-10)
# =====================================================================
#  Jahongir: "Maksimal ball bor o'tish balli yo'qku" -> "test turi
#  boyivha sozlamalarda bir marta, foizda olchanadi, 65% unit testda
#  60% esa mid va end courselarda".
#
#  Bu — birinchi ishga tushirishdagi STANDART qiymat. Keyin asoschi
#  Gamification -> Coin qoidasi sahifasidan o'zgartiradi.
#
#  Mock yo'q: u IELTS band bilan baholanadi, o'tish foizi qo'llanmaydi.
DEFAULT_EXAM_PASS = {"unit": 65.0, "mid": 60.0, "end": 60.0}

#  ESKI TESTLAR uchun chegara (pass_percent muhrlanmagan yozuvlar).
#  Ular yaratilgan paytda alohida maydon yo'q edi va ikki xil qotirilgan
#  raqam ishlagan: hisobotda 65%, sertifikatda LEVEL_PASS_PERCENT.
#  Tarix o'zgarmasligi uchun ular o'sha holicha qoldiriladi.
LEGACY_EXAM_PASS_REPORT = 65.0


def exam_pass_percent(exam, default: float | None = None):
    """Bitta imtihonning o'tish foizi.

    Muhrlangan bo'lsa — o'sha; bo'lmasa (eski test) — `default`.
    Mock uchun None: band bilan baholanadi."""
    if exam is None:
        return default
    if getattr(exam, "kind", None) == "mock":
        return None
    v = getattr(exam, "pass_percent", None)
    return default if v is None else v


# "Oylik test o'rtachasi" qancha kunlik oynada olinadi
TEST_WINDOW_DAYS = 30
# O'quvchilarning bosqichdan o'tishi qancha oy orqaga qarab hisoblanadi
PASS_WINDOW_MONTHS = 12

GRADE_EVENT_KINDS = [
    ("promote", "Ko'tarildi", "emerald"),
    ("demote", "Tushirildi", "red"),
    ("set", "Qo'lda belgilandi", "slate"),
    ("remediation", "Qayta tayyorlashga qo'yildi", "amber"),
    ("remediation_done", "Qayta tayyorlash tugadi", "sky"),
]
GRADE_EVENT_LABELS = {k: lbl for k, lbl, _ in GRADE_EVENT_KINDS}
GRADE_EVENT_TONE = {k: t for k, _, t in GRADE_EVENT_KINDS}

# ---- O'qish rejasi: kitob va podkast --------------------------------
# Support -> Teacher bosqichi uchun. Bularsiz va imtihonsiz
# teacherlikka o'tilmaydi.
TEACHER_BOOKS = [
    "Learning Teaching",
    "Teach Like a Champion",
    "Teach Like a Pirate",
    "What Works in Schools",
]
TEACHER_PODCASTS = [
    "Isroil Bo'riyev (Everest)",
    "Doniyor Aslanov (Everest)",
    "Bekzod Mirahmedov (Everest)",
    "Oysara Ravshanova (Everest)",
    "Mohira Nabiyeva (Everest)",
    "Intizor Urokova (Everest)",
    "Farrukh Rustamov (Everest)",
    "Xumoyunmirzo Xolmaxamatov (Everest)",
    "Sirojiddin Malikov (Everest)",
    "Nodirjon Egamberdiyev (Everest)",
    "IELTS 8.5 PODCAST | SELF-STUDY (Everest)",
    "O'zbekistonda ilk bora IELTS 8.5 Instruktorlar bilan Podcast (Everest)",
]
HEAD_BOOKS = [
    "Why Don't Students Like School?",
    "Visible Learning and the Science of How We Learn",
    "Teach Like a Champion 2.0",
    "Building a Better Teacher",
]
HEAD_PODCASTS = [
    "Edu podcast 4-son",
    "Edu podcast 5-son",
    "Edu podcast 7-son",
    "Edu podcast 10-son",
    "Edu podcast 11-son",
    "Edu podcast 12-son",
    "Edu podcast 13-son",
]

STUDY_STAGES = [
    ("teacher", "Teacherlik bosqichi", TEACHER_BOOKS, TEACHER_PODCASTS),
    ("head", "Head teacherlik bosqichi", HEAD_BOOKS, HEAD_PODCASTS),
]
STUDY_STAGE_LABELS = {k: lbl for k, lbl, _, _ in STUDY_STAGES}

# Hujjatda kitoblar "lavozimi PAYTIDA o'qilishi kerak" deb yozilgan.
# Shuning uchun ro'yxat o'sha bosqichdan CHIQISHDA tekshiriladi:
# teacherlik ro'yxati Junior'dan yuqoriga o'tishda, head ro'yxati esa
# Head'dan Metodistga o'tishda.
STUDY_REQUIRED_FOR = {"middle": "teacher", "metodist": "head"}

CAREER_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, HR_MANAGER, BRANCH_MANAGER]
GRADE_ADMIN = FULL_ACCESS + [ACADEMIC_HEAD]


# =====================================================================
#  Ustozlar reytingi
#  Ustoz o'z natijasini va hamkasblari orasidagi o'rnini ko'radi -
#  lekin ularning MAOSHINI ko'rmaydi.
# =====================================================================
TEACHER_SCORE_WEIGHTS = [
    ("quality", "Dars sifati", 40),
    ("retention", "O'quvchi saqlanishi", 30),
    ("ltv", "O'quvchi qiymati (LTV)", 20),
    ("attendance", "Davomat", 10),
]
TEACHER_SCORE_LABELS = {k: lbl for k, lbl, _ in TEACHER_SCORE_WEIGHTS}
TEACHER_SCORE_DEFAULT = {k: w for k, _, w in TEACHER_SCORE_WEIGHTS}


# =====================================================================
#  RUXSATLAR MATRITSASI
#
#  Har bir ROL uchun har bir BO'LIMDA nima qila olishi belgilanadi.
#  Buni faqat ASOSCHI o'zgartiradi.
#
#  Amallar:
#    view    - ko'rish
#    create  - yaratish
#    edit    - tahrirlash
#    delete  - o'chirish
#    approve - tasdiqlash
#    export  - eksport qilish
#    secret  - maxfiy maydonlarni ko'rish (maosh, foyda, karta raqami)
# =====================================================================

PERM_ACTIONS = [
    ("view", "Ko'rish"),
    ("create", "Yaratish"),
    ("edit", "Tahrirlash"),
    ("delete", "O'chirish"),
    ("approve", "Tasdiqlash"),
    ("export", "Eksport"),
    ("secret", "Maxfiy maydonlar"),
]
PERM_ACTION_LABELS = dict(PERM_ACTIONS)
PERM_ACTION_KEYS = [k for k, _ in PERM_ACTIONS]

# Bo'limlar: (kalit, nomi, guruh)
RESOURCES = [
    ("dashboard", "Dashboard", "Umumiy"),
    ("timetable", "Dars jadvali", "Umumiy"),
    ("tasks", "Vazifalar", "Umumiy"),
    ("coins", "Coin va sovg'alar", "Umumiy"),

    ("leads", "Lidlar", "Sotuv"),
    ("students", "O'quvchilar", "Sotuv"),
    ("groups", "Guruhlar", "Sotuv"),
    ("marketing", "Marketing", "Sotuv"),

    ("payments", "To'lovlar", "Moliya"),
    ("debtors", "Qarzdorlar", "Moliya"),
    ("expenses", "Xarajatlar", "Moliya"),
    ("pnl", "Foyda / zarar", "Moliya"),
    ("salary", "Ish haqi", "Moliya"),
    ("discounts", "Chegirmalar", "Moliya"),

    ("teachers", "O'qituvchilar", "O'quv"),
    ("academic", "O'quv bo'limi", "O'quv"),
    ("exams", "Imtihonlar", "O'quv"),
    ("attendance", "Yo'qlama", "O'quv"),
    ("grades", "Baholar", "O'quv"),

    ("staff", "Xodimlar", "Boshqaruv"),
    ("hr", "HR", "Boshqaruv"),
    ("inventory", "Ombor va aktivlar", "Boshqaruv"),
    ("branches", "Filiallar", "Boshqaruv"),
    ("reports", "Hisobotlar", "Boshqaruv"),
    ("events", "Tadbirlar va tug'ilgan kunlar", "Boshqaruv"),
    ("audit", "Audit", "Boshqaruv"),
    ("permissions", "Ruxsatlar", "Boshqaruv"),
]
RESOURCE_LABELS = {k: lbl for k, lbl, _ in RESOURCES}
RESOURCE_KEYS = [k for k, _, _ in RESOURCES]
RESOURCE_GROUPS = {k: g for k, _, g in RESOURCES}

# Maxfiy maydon nima ekanini odam tushunishi uchun
SECRET_HINTS = {
    "salary": "Boshqa xodimlarning maoshi",
    "pnl": "Sof foyda va rentabellik",
    "payments": "To'lov kartasi ma'lumotlari",
    "students": "Ota-ona telefoni va manzili",
    "staff": "Shaxsiy hujjat ma'lumotlari",
    "hr": "Nomzodning kutilayotgan maoshi",
}


def _p(*actions) -> set:
    return set(actions)


V = _p("view")
VE = _p("view", "export")
VC = _p("view", "create")
VCE = _p("view", "create", "edit")
VCEX = _p("view", "create", "edit", "export")
VCED = _p("view", "create", "edit", "delete")
ALL_P = set(PERM_ACTION_KEYS)


# Standart matritsa. Asoschi bu yerda YO'Q - unga hamma narsa ochiq
# va uni o'zgartirib bo'lmaydi.
DEFAULT_MATRIX: dict = {
    FINANCE_DIRECTOR: {
        "dashboard": VE, "timetable": V, "tasks": VCED,
        "leads": VE, "students": VE, "groups": V, "marketing": VE,
        "payments": ALL_P, "debtors": ALL_P, "expenses": ALL_P,
        "pnl": ALL_P, "salary": ALL_P, "discounts": ALL_P,
        "teachers": VE, "academic": V, "exams": V,
        "staff": VE, "hr": V, "inventory": VE, "branches": VE,
        "reports": VE, "audit": VE,
    },
    ACCOUNTANT: {
        "dashboard": V, "timetable": V, "tasks": VCE,
        "students": V, "groups": V,
        "payments": VCEX, "debtors": VCEX, "expenses": VCEX,
        "salary": VCEX, "discounts": V,
        "inventory": VE, "reports": VE,
    },
    BRANCH_MANAGER: {
        "dashboard": VE, "timetable": VCED, "tasks": VCED, "coins": ALL_P,
        "leads": VCEX, "students": ALL_P, "groups": ALL_P,
        "marketing": VE,
        "payments": ALL_P, "debtors": ALL_P, "expenses": VCEX,
        "pnl": VE, "salary": VCEX, "discounts": ALL_P,
        "teachers": VCEX, "academic": VCED, "exams": VE,
        "attendance": VCE, "grades": VCE,
        "staff": VE, "hr": V, "inventory": VCED, "branches": V,
        "reports": VE, "audit": VE,
    },
    SALES_HEAD: {
        "dashboard": VE, "timetable": V, "tasks": VCED,
        "leads": ALL_P, "students": VCEX, "groups": VE,
        "marketing": VCEX,
        "payments": VC, "debtors": VCEX, "discounts": VC,
        "teachers": V, "reports": VE,
    },
    SALES_MANAGER: {
        "dashboard": V, "timetable": V, "tasks": VCE, "coins": VCE,
        "leads": VCEX, "students": VCE, "groups": V,
        "payments": VC, "debtors": VCE, "discounts": VC,
        "teachers": V,
    },
    ADMINISTRATOR: {
        "dashboard": V, "timetable": V, "tasks": VCE, "coins": VCE,
        "leads": VCE, "students": VCE, "groups": V,
        "payments": VC, "debtors": VCE,
        "attendance": VCE,
        "teachers": V, "inventory": V,
    },
    SMM_MANAGER: {
        "dashboard": V, "tasks": VCE,
        "leads": VCE, "marketing": ALL_P, "students": V,
        "reports": VE,
    },
    ACADEMIC_HEAD: {
        "dashboard": VE, "timetable": VCED, "tasks": VCED, "coins": VCED,
        "students": VCE, "groups": VCE,
        "teachers": VCEX, "academic": ALL_P, "exams": VE,
        "attendance": VCED, "grades": VCED,
        "inventory": V, "reports": VE,
    },
    TEACHER: {
        "dashboard": V, "timetable": V, "tasks": VCE, "coins": V,
        "students": V, "groups": V,
        "attendance": VCE, "grades": VCE, "exams": VC,
        "academic": V,
    },
    SUPPORT_TEACHER: {
        "dashboard": V, "timetable": V, "tasks": VCE, "coins": VCE,
        "leads": VCE, "students": V, "groups": V,
        "attendance": VCE, "grades": VCE, "academic": VCE,
        "inventory": V,
    },
    HEAD_SUPPORT: {
        "dashboard": VE, "timetable": V, "tasks": VCED, "coins": VCED,
        "leads": VCE, "students": VCE, "groups": V,
        "attendance": VCED, "grades": VCE, "academic": VCED,
        "teachers": V, "inventory": V, "reports": VE,
    },
    EXAMINER: {
        "dashboard": V, "timetable": V, "tasks": VCE,
        "students": V, "groups": V,
        "exams": VCED, "grades": VCE, "academic": V,
    },
    HEAD_EXAMINER: {
        "dashboard": VE, "timetable": V, "tasks": VCED,
        "students": V, "groups": V, "teachers": V,
        "exams": ALL_P, "grades": VCED, "academic": VE,
        "reports": VE, "audit": V,
    },
    HR_MANAGER: {
        "dashboard": VE, "timetable": V, "tasks": VCED,
        "staff": ALL_P, "hr": ALL_P, "salary": VE,
        "teachers": VE, "inventory": VCED, "reports": VE,
    },
    FACILITY_MANAGER: {
        "dashboard": V, "timetable": V, "tasks": VCE,
        "inventory": ALL_P, "expenses": VC, "branches": V,
    },
    EVENT_MANAGER: {
        "tasks": VCE, "events": ALL_P, "students": V, "staff": V,
        "branches": V,
    },
    # Ota-ona va o'quvchi - faqat o'ziga tegishlini ko'radi.
    # Bu chegara kodda ham qattiq turadi: matritsani ochib qo'yish
    # ularga BOSHQA odamning ma'lumotini ko'rsatmaydi.
    PARENT: {
        "dashboard": V, "timetable": V,
        "students": V, "payments": V, "attendance": V, "grades": V,
        "exams": V, "coins": V,
    },
    STUDENT: {
        "dashboard": V, "timetable": V,
        "attendance": V, "grades": V, "exams": V,
        # Coin do'koni: ko'radi va sovg'a so'raydi (yaratish)
        "coins": VC,
    },
}


def default_perms(role: str, resource: str) -> set:
    """Kod bilan keladigan standart ruxsat."""
    if role == FOUNDER:
        return set(ALL_P)
    return set(DEFAULT_MATRIX.get(role, {}).get(resource, set()))


# Asoschidan olib bo'lmaydigan ruxsatlar - aks holda tizimga kirish
# yo'li yopilib qolishi mumkin.
LOCKED_ROLE = FOUNDER


# =====================================================================
#  LTV — mijoz qancha vaqt qoladi va qancha pul keltiradi
#
#  Ikki xil LTV bor va ular chalkashmasligi kerak:
#    VAQT LTV  - o'quvchi o'rtacha necha oy qoladi
#    PUL LTV   - shu vaqt ichida qancha to'laydi va qancha SOF FOYDA
#                qoldiradi (ustoz haqi va boshqa xarajatlar chiqarilgach)
# =====================================================================
LTV_DIMENSIONS = [
    ("overall", "Butun markaz"),
    ("branch", "Filiallar"),
    ("teacher", "Ustozlar"),
    ("subject", "Fanlar"),
    ("group", "Guruhlar"),
]
LTV_DIMENSION_LABELS = dict(LTV_DIMENSIONS)

# Sof foydani hisoblash uchun: umumiy xarajatning necha foizi bitta
# o'quvchiga to'g'ri keladi. Ustoz haqi alohida hisoblanadi, qolgan
# xarajat (ijara, kommunal, reklama) o'quvchilar soniga bo'linadi.
LTV_ACCESS = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT, ACADEMIC_HEAD,
                            SALES_HEAD]


# =====================================================================
#  Xodimlar davomati
# =====================================================================
WORK_START = "09:00"     # standart ish boshlanishi
WORK_END = "18:00"       # standart ish tugashi
LATE_TOLERANCE_MIN = 5   # 5 daqiqagacha kechikish - kechikish emas

ATTENDANCE_ACCESS = FULL_ACCESS + [HR_MANAGER]


# =====================================================================
#  NPS — ustozga berilgan baho
#  0-10 shkala. 9-10 tarafdor, 7-8 betaraf, 0-6 tanqidchi.
#  NPS = tarafdorlar% - tanqidchilar%
# =====================================================================
NPS_SOURCES = [
    ("student", "O'quvchi"),
    ("parent", "Ota-ona"),
]
NPS_SOURCE_LABELS = dict(NPS_SOURCES)

NPS_BANDS = [
    (9, "promoter", "Tarafdor", "emerald"),
    (7, "passive", "Betaraf", "amber"),
    (0, "detractor", "Tanqidchi", "red"),
]


def nps_band(score: int) -> tuple:
    for minimum, key, label, tone in NPS_BANDS:
        if score >= minimum:
            return key, label, tone
    return "detractor", "Tanqidchi", "red"


def nps_value(scores: list) -> float:
    """NPS = tarafdorlar foizi - tanqidchilar foizi. -100 dan +100 gacha."""
    if not scores:
        return 0.0
    pro = sum(1 for s in scores if s >= 9)
    det = sum(1 for s in scores if s <= 6)
    return round((pro - det) / len(scores) * 100, 1)


NPS_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, HR_MANAGER, HEAD_SUPPORT]


# =====================================================================
#  Ketish sabablari (churn)
#  Sababsiz raqam hech narsani o'zgartirmaydi: "10 kishi ketdi" emas,
#  "10 kishi ustoz almashgani uchun ketdi" degani qaror keltiradi.
# =====================================================================
LEAVE_REASONS = [
    ("price", "Narx qimmat", "money"),
    ("teacher", "Ustozdan norozi", "quality"),
    ("schedule", "Vaqti to'g'ri kelmadi", "logistics"),
    ("distance", "Uzoq", "logistics"),
    ("result", "Natija ko'rmadi", "quality"),
    ("moved", "Ko'chib ketdi", "external"),
    ("finished", "Kursni tugatdi", "good"),
    ("competitor", "Boshqa markazga ketdi", "quality"),
    ("family", "Oilaviy sabab", "external"),
    # 2026-08-30, Jahongir: "o'quv markazdan ketish sababi ichiga
    # JONY SCHOOL MAKTABIGA O'TDI va BOSHQA XUSUSIY MAKTABGA O'TDI
    # sabablarini ham qo'shish kerak".
    #
    # Ikkalasi ham "maktabga o'tdi", lekin biznes uchun YERU-OSMON
    # farq qiladi:
    #   · Jony School — BIZNING maktabimiz. Bola markazdan chiqdi,
    #     lekin kompaniyadan chiqmadi. Bu yo'qotish EMAS, ichki
    #     ko'chish. Shuning uchun alohida guruh: "internal".
    #   · Boshqa xususiy maktab — haqiqiy yo'qotish, lekin bizga
    #     bog'liq emas (ota-ona ta'lim shaklini almashtirdi).
    ("jony_school", "Jony School maktabimizga o'tdi", "internal"),
    ("private_school", "Boshqa xususiy maktabga o'tdi", "external"),
    ("unknown", "Sababi noma'lum", "unknown"),
]
LEAVE_REASON_LABELS = {k: lbl for k, lbl, _ in LEAVE_REASONS}
LEAVE_REASON_GROUP = {k: g for k, _, g in LEAVE_REASONS}

# Bizga bog'liq sabablar - shularni kamaytirish mumkin
CONTROLLABLE_REASONS = ["teacher", "result", "competitor", "schedule"]

# Sabab guruhlarining nomlari — statistikada shu bilan ko'rinadi
LEAVE_GROUP_LABELS = {
    "money": "Pul",
    "quality": "Sifat (bizga bog'liq)",
    "logistics": "Qulaylik",
    "external": "Tashqi sabab",
    "internal": "Ichki ko'chish (yo'qotish emas)",
    "good": "Yaxshi yakun",
    "unknown": "Noma'lum",
}

# YO'QOTISH DEB HISOBLANMAYDIGANLAR. Kursni tugatgan bola ham,
# Jony School maktabimizga o'tgan bola ham "ketgan" emas —
# churn foizini bularsiz ko'rish kerak, aks holda raqam
# haqiqatdan yomonroq ko'rinadi.
NOT_CHURN_REASONS = ["finished", "jony_school"]


# =====================================================================
#  Muzlatish sabablari (2026-08-30, Jahongir: "muzlatish sabablari
#  statistikasi ham kerak")
#
#  Ilgari muzlatishda faqat erkin izoh bor edi — har kim har xil
#  yozardi va statistika yig'ib bo'lmasdi. Endi ro'yxat, izoh esa
#  qo'shimcha bo'lib qoladi.
# =====================================================================
FREEZE_REASONS = [
    ("vacation", "Ta'til / dam olish", "planned"),
    ("illness", "Kasallik", "external"),
    ("money", "Vaqtincha pul qiyinchiligi", "money"),
    ("school_load", "Maktab/universitet yuklamasi", "logistics"),
    ("exam_period", "Imtihon davri", "logistics"),
    ("travel", "Safar / boshqa shaharda", "external"),
    ("schedule", "Dars vaqti to'g'ri kelmadi", "logistics"),
    ("absent", "Darsga kelmagani uchun (avtomat)", "risk"),
    ("family", "Oilaviy sabab", "external"),
    ("other", "Boshqa sabab", "unknown"),
]
FREEZE_REASON_LABELS = {k: lbl for k, lbl, _ in FREEZE_REASONS}
FREEZE_REASON_GROUP = {k: g for k, _, g in FREEZE_REASONS}
FREEZE_GROUP_LABELS = {
    "planned": "Rejali",
    "external": "Tashqi sabab",
    "money": "Pul",
    "logistics": "Qulaylik",
    "risk": "Xavf belgisi",
    "unknown": "Noma'lum",
}
# Ketish xavfi yuqori bo'lgan muzlatishlar — bularni kuzatish kerak
FREEZE_RISK_REASONS = ["money", "absent", "schedule"]


# =====================================================================
#  LIDNI O'CHIRISH SABABLARI (2026-08-30, Jahongir: "lidni
#  o'chirishni ham sabablar qo'shib qo'y, ichida ADASHIB KIRITILIB
#  YUBORILIBDI bo'lsin")
#
#  NEGA MUHIM. Lid o'chirilganda voronka statistikasi o'zgaradi.
#  "Adashib kiritilgan" yozuv — umuman lid EMAS edi, uni yo'qotish
#  deb sanash noto'g'ri. Dubl ham shunday. Qolganlari esa haqiqiy
#  lid bo'lgan va yo'qolgan — ular kuzatilishi kerak.
#
#  Shuning uchun uchinchi ustun: bu HAQIQIY YO'QOTISHMI.
LEAD_DELETE_REASONS = [
    ("mistake", "Adashib kiritib yuborilgan", False),
    ("duplicate", "Dubl (allaqachon bazada bor)", False),
    ("test", "Sinov / tekshiruv yozuvi", False),
    ("spam", "Spam yoki soxta ariza", False),
    ("wrong_number", "Telefon raqami noto'g'ri", True),
    ("no_answer", "Ko'p marta ko'tarmadi", True),
    ("not_interested", "Qiziqmadi", True),
    ("competitor", "Boshqa markazni tanladi", True),
    ("other", "Boshqa sabab", True),
]
LEAD_DELETE_LABELS = {k: lbl for k, lbl, _ in LEAD_DELETE_REASONS}
# Statistikada "haqiqiy yo'qotilgan lid" deb sanaladiganlar
LEAD_DELETE_REAL = [k for k, _l, real in LEAD_DELETE_REASONS if real]


# =====================================================================
#  ROMI — reklama samaradorligi
#  ROMI = (kanal keltirgan foyda - kanal xarajati) / kanal xarajati x 100
# =====================================================================
ROMI_BANDS = [
    (200, "great", "Zo'r", "emerald"),
    (100, "good", "Yaxshi", "sky"),
    (0, "weak", "Zaif", "amber"),
    (-10000, "loss", "Zarar", "red"),
]


def romi_band(value: float) -> tuple:
    for minimum, key, label, tone in ROMI_BANDS:
        if value >= minimum:
            return key, label, tone
    return "loss", "Zarar", "red"


# =====================================================================
#  RFM segmentatsiya
#  R (Recency)   - oxirgi to'lovdan beri qancha vaqt o'tdi
#  F (Frequency) - nechta to'lov qilgan
#  M (Monetary)  - jami qancha to'lagan
#  Har biri 1-3 ball. Segment - shu uch balldan chiqadi.
# =====================================================================
RFM_SEGMENTS = [
    ("champion", "Eng yaxshi mijoz", "Yaqinda to'lagan, ko'p to'lagan",
     "emerald", "Sovg'a va referral taklifi"),
    ("loyal", "Sodiq mijoz", "Muntazam to'laydi",
     "sky", "Uzoq muddatli chegirma taklif qiling"),
    ("potential", "Istiqbolli", "Yangi, lekin faol",
     "violet", "Qo'shimcha kursga taklif qiling"),
    ("attention", "E'tibor kerak", "To'lovi kechikyapti",
     "amber", "Qo'ng'iroq qiling"),
    ("sleeping", "Uxlab qolgan", "Uzoq vaqt to'lov yo'q",
     "orange", "Qaytarish taklifi yuboring"),
    ("lost", "Ketgan", "Ancha vaqtdan beri yo'q",
     "red", "Nega ketganini so'rang"),
]
RFM_SEGMENT_LABELS = {k: lbl for k, lbl, _, _, _ in RFM_SEGMENTS}
RFM_SEGMENT_INFO = {k: {"label": lbl, "hint": h, "tone": t, "action": a}
                    for k, lbl, h, t, a in RFM_SEGMENTS}


def rfm_score(days_since: int, count: int, total: float,
              money_step: float = 1_000_000) -> tuple:
    """R, F, M ballari (1-3) va segment."""
    r = 3 if days_since <= 30 else 2 if days_since <= 60 else 1
    f = 3 if count >= 6 else 2 if count >= 3 else 1
    m = 3 if total >= money_step * 3 else 2 if total >= money_step else 1

    if r == 3 and f >= 2 and m >= 2:
        seg = "champion"
    elif r >= 2 and f >= 2:
        seg = "loyal"
    elif r == 3:
        seg = "potential"
    elif r == 2:
        seg = "attention"
    elif days_since <= 120:
        seg = "sleeping"
    else:
        seg = "lost"
    return r, f, m, seg


# =====================================================================
#  Avtomatik xabarnomalar
#  Tizim xabarni o'zi yaratadi va navbatga qo'yadi. Yuborish uchun
#  Telegram bot tokeni yoki SMS xizmati kerak.
# =====================================================================
NOTIFY_KINDS = [
    ("birthday", "Tug'ilgan kun tabrigi", 0),
    ("payment_due", "To'lov eslatmasi", 3),
    ("debt", "Qarzdorlik haqida", 0),
    ("new_course", "Yangi kurs haqida", 0),
    ("absence", "Darsga kelmadi", 0),
    ("certificate", "Sertifikat tabrigi", 0),
    ("comeback", "Qaytishga taklif", 0),
]
NOTIFY_KIND_LABELS = {k: lbl for k, lbl, _ in NOTIFY_KINDS}
NOTIFY_DEFAULT_DAYS = {k: d for k, _, d in NOTIFY_KINDS}

NOTIFY_CHANNELS = [
    ("telegram", "Telegram"),
    ("sms", "SMS"),
]
NOTIFY_CHANNEL_LABELS = dict(NOTIFY_CHANNELS)

NOTIFY_STATUSES = [
    ("queued", "Navbatda", "amber"),
    ("sent", "Yuborildi", "emerald"),
    ("failed", "Yuborilmadi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
NOTIFY_STATUS_LABELS = {k: lbl for k, lbl, _ in NOTIFY_STATUSES}
NOTIFY_STATUS_TONE = {k: t for k, _, t in NOTIFY_STATUSES}

# Standart shablonlar. {ism}, {summa}, {sana}, {guruh}, {kurs}
DEFAULT_TEMPLATES = {
    "birthday": (
        "Tug'ilgan kun muborak!",
        "{ism}, tug'ilgan kuningiz muborak bo'lsin! Jony Academy "
        "jamoasi sizga sog'lik va katta yutuqlar tilaydi."),
    "payment_due": (
        "To'lov eslatmasi",
        "Assalomu alaykum. {ism} uchun {sana} gacha {summa} so'm "
        "to'lov kutilmoqda. Rahmat!"),
    "debt": (
        "Qarzdorlik",
        "Assalomu alaykum. {ism} bo'yicha {summa} so'm qarzdorlik "
        "bor. Iltimos, qulay vaqtda to'lab qo'ying."),
    "new_course": (
        "Yangi kurs",
        "{ism}, {kurs} kursi ochildi. Qiziqsangiz — biz bilan "
        "bog'laning."),
    "absence": (
        "Darsga kelmadi",
        "Assalomu alaykum. {ism} bugungi darsga kelmadi. "
        "Hammasi joyidami?"),
    "certificate": (
        "Tabriklaymiz!",
        "{ism}, natijangiz bilan tabriklaymiz! Sertifikatingiz "
        "tayyor — markazdan olib ketishingiz mumkin."),
    "comeback": (
        "Sizni sog'indik",
        "{ism}, ancha vaqtdan beri ko'rinmaysiz. Qaytib kelsangiz "
        "— birinchi oyga chegirma bor."),
}

NOTIFY_ACCESS = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
                               ADMINISTRATOR]


# =====================================================================
#  Referral tizimi
#  "Do'stingni olib kel va chegirma ol"
# =====================================================================
REFERRAL_PERCENT = 10.0          # olib kelganga beriladigan chegirma
REFERRAL_MONTHS = 1              # necha oy amal qiladi
# Do'sti kelgani hisoblanishi uchun u qancha to'lashi kerak — aks holda
# faqat ro'yxatdan o'tib, keyin ketib qolgan odam uchun ham chegirma
# berilib ketardi.
REFERRAL_MIN_PAYMENT = 1

# MARKETOLOGGA FOYDALI HISOBOTLAR (2026-08-27).
#
# Jahongir: "Smm mutaxasisi uchun hisobotlardan va analitikadan
# qismida unga kerakli foydali boladiganlari korsatilsin."
#
# Bu ro'yxatga FAQAT marketing ishiga kerak bo'lgan hisobotlar
# kiradi: lid manbalari, jalb qilish voronkasi, hayot davri, sotuv
# voronkasi va bitta lid narxi (CAC). Foyda-zarar, oyliklar va
# xodimlar KPI'si bu yerga KIRMAYDI — ular marketolog ishi emas
# va pul ma'lumoti keraksiz joyga tarqalmasligi kerak.
MARKETING_REPORTS = FINANCE_ACCESS + [SMM_MANAGER, SALES_HEAD]

MARKETING_ANALYTICS = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD,
                                     FINANCE_DIRECTOR]


# =====================================================================
#  XODIMLARNING SANALARI — tug'ilgan kun va ish yubileyi
#
#  Odam esdan chiqarishi mumkin, tizim esdan chiqarmaydi. Sana
#  yaqinlashganda HR'ga vazifa o'zi paydo bo'ladi — bir necha kun
#  oldindan, ulgurish uchun. Tayyor tabrik matni ham vazifa ichida
#  turadi: HR ko'chirib yuboradi, o'ylab o'tirmaydi.
# =====================================================================
STAFF_DATE_LEAD_DAYS = 5          # necha kun oldin eslatiladi
STAFF_DATE_HORIZON = 60           # ro'yxatda necha kunlik oldinni ko'rsatamiz

STAFF_DATE_KINDS = [
    ("birthday", "Tug'ilgan kun", "violet"),
    ("anniversary", "Ish yubileyi", "sky"),
]
STAFF_DATE_LABELS = {k: lbl for k, lbl, _ in STAFF_DATE_KINDS}
STAFF_DATE_TONE = {k: t for k, _, t in STAFF_DATE_KINDS}

# Sanalarni HR ko'radi. Filial rahbari o'z filialidagilarni ko'radi.
STAFF_DATES_ACCESS = FULL_ACCESS + [HR_MANAGER, BRANCH_MANAGER]

UZ_MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul",
             "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def exam_title(kind: str, unit_no: int | None = None) -> str:
    """Imtihon sarlavhasi — frontenddagi examTitle bilan bir xil."""
    if kind == "unit" and unit_no:
        return f"Unit {unit_no}"
    return EXAM_KIND_LABELS.get(kind, kind)


def uz_date(d) -> str:
    """12-avgust. Yil yozilmaydi — har yili takrorlanadigan sana."""
    if not d:
        return "—"
    return f"{d.day}-{UZ_MONTHS[d.month - 1]}"


def next_occurrence(d, today):
    """Sananing keyingi kelishi. 29-fevral bo'lsa — 28-fevralga
    suriladi, aks holda kabisa bo'lmagan yili eslatma umuman
    chiqmay ketardi."""
    if not d:
        return None

    def _try(year):
        try:
            return d.replace(year=year)
        except ValueError:          # 29-fevral, kabisa emas yil
            return d.replace(year=year, day=28)

    nxt = _try(today.year)
    if nxt < today:
        nxt = _try(today.year + 1)
    return nxt


def tenure_text(hired, on) -> str:
    """Ishga kirganidan beri qancha vaqt o'tgani — odam tilida."""
    if not hired or not on:
        return "—"
    months = (on.year - hired.year) * 12 + (on.month - hired.month)
    if on.day < hired.day:
        months -= 1
    if months < 0:
        months = 0
    y, m = divmod(months, 12)
    if y and m:
        return f"{y} yil {m} oy"
    if y:
        return f"{y} yil"
    if m:
        return f"{m} oy"
    return "endi keldi"


# =====================================================================
#  Umumiy dashboard raqamlari
#
#  Butun markaz bo'yicha raqamlar (o'quvchilar soni, tushum, qarzdorlar,
#  xodimlar soni) HAMMAGA kerak emas. Examinerga imtihon, HR'ga xodim,
#  SMM'ga marketing kerak — birovning raqami ularni chalg'itadi.
# =====================================================================
GENERAL_DASHBOARD = FULL_ACCESS + [
    FINANCE_DIRECTOR, ACCOUNTANT,
    SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
    ACADEMIC_HEAD,
]


# =====================================================================
#  COIN DO'KONI — o'quvchi coiniga oladigan sovg'alar
#
#  Ro'yxat rasmdagi plakatdan olingan. Narx o'zgarsa — Coin tizimi
#  bo'limidan tahrirlanadi, bu yerdagi ro'yxat faqat BOSHLANG'ICH
#  holat: bir marta bazaga tushadi va keyin qo'l tegmaydi.
# =====================================================================
REWARD_CATEGORIES = [
    ("merch", "Jony Academy buyumlari", "teal"),
    ("tech", "Texnika", "sky"),
    ("sport", "Sport va o'yin", "emerald"),
    ("special", "Maxsus sovg'alar", "violet"),
]
REWARD_CATEGORY_LABELS = {k: lbl for k, lbl, _ in REWARD_CATEGORIES}
REWARD_CATEGORY_TONE = {k: t for k, _, t in REWARD_CATEGORIES}

# (nomi, coin, kategoriya)
DEFAULT_REWARDS = [
    # --- 50-100 coin: kundalik buyumlar ---
    ("Course book", 50, "merch"),
    ("Kepka", 50, "merch"),
    ("Krujka", 50, "merch"),
    ("Essay daftar", 50, "merch"),
    ("Kofe stakan", 70, "merch"),
    ("33% chegirma kartasi", 100, "special"),
    ("Jony bloknot va ruchka", 100, "merch"),
    ("Futbolka", 100, "merch"),
    ("Sviter", 150, "merch"),
    ("Xudi", 200, "merch"),

    # --- 200-400 coin ---
    ("Smart soat", 200, "tech"),
    ("Joynamoz va do'ppi", 200, "special"),
    ("Flesh karta", 200, "tech"),
    ("To'p (futbol yoki basketbol)", 300, "sport"),
    ("Sumka", 300, "merch"),
    ("Kolonka", 300, "tech"),
    ("Portfel", 300, "merch"),
    ("Quloqchin", 300, "tech"),
    ("AirPods", 400, "tech"),

    # --- 500-1000 coin ---
    ("Tashakkurnoma", 500, "special"),
    ("CEFR to'lovi", 500, "special"),
    ("Qur'on kolonka", 700, "special"),
    ("Shaxmat", 800, "sport"),
    ("Karaoke klub", 1000, "sport"),
    ("O'quvchi haqida video", 1000, "special"),

    # --- Katta sovg'alar ---
    ("IELTS to'lovi", 2000, "special"),
    ("iPod", 3000, "tech"),
    ("Telefon", 4000, "tech"),
    ("Noutbuk", 5000, "tech"),
    ("Jony bilan kechki ovqat", 5000, "special"),
]


# =====================================================================
#  Sovg'a so'rovining holati
#
#  O'quvchi o'zi tanlaydi, lekin sovg'a qo'lma-qo'l beriladi. Shuning
#  uchun ikki bosqich: SO'RALDI -> BERILDI. So'ralgan paytda coin
#  BAND qilinadi — aks holda bir coinni ikki marta sarflash mumkin
#  bo'lib qolardi.
# =====================================================================
REDEEM_STATUSES = [
    ("requested", "So'raldi", "amber"),
    ("given", "Berildi", "emerald"),
    ("rejected", "Rad etildi", "red"),
]
REDEEM_STATUS_LABELS = {k: lbl for k, lbl, _ in REDEEM_STATUSES}
REDEEM_STATUS_TONE = {k: t for k, _, t in REDEEM_STATUSES}

# =====================================================================
#  YUTUQLAR (BADGE) VA STREAK SOVRINLARI (2026-08-16)
#
#  Jahongir: "Qo'shilishi kerak bo'lgan gamification elementlari:
#  ... 7, 14, 30 kunlik streak sovrinlari; badge va achievement'lar
#  ... 'Yana 10 XP va sovrin ochiladi' kabi yaqin maqsad."
#
#  MUHIM QAROR: yutuqlar uchun YANGI JADVAL OCHILMADI. Har bir
#  yutuq mavjud yozuvlardan HISOBLANADI (streak, lug'at javoblari,
#  grammatika mavzulari, XP, davomat, imtihon). Sabablari:
#    - migratsiya xavfi yo'q;
#    - eski o'quvchilar ham darrov o'z yutuqlarini ko'radi
#      (orqaga qarab hisoblanadi);
#    - ma'lumot dublikat bo'lmaydi, ikki joyda ikki xil son chiqmaydi.
#
#  (kalit, sarlavha, izoh, o'lchov, maqsad, belgi, rang)
#  o'lchov: streak | vocab | grammar_topics | xp | lessons | exams
# =====================================================================
BADGES = [
    ("streak_7",    "Bir hafta uzluksiz", "7 kun ketma-ket lug'at mashqi",
     "streak", 7, "flame", "amber"),
    ("streak_14",   "Ikki hafta uzluksiz", "14 kun ketma-ket lug'at mashqi",
     "streak", 14, "flame", "orange"),
    ("streak_30",   "Bir oy uzluksiz", "30 kun ketma-ket lug'at mashqi",
     "streak", 30, "flame", "red"),

    ("vocab_100",   "100 ta to'g'ri javob", "Lug'at mashqlarida 100 ta to'g'ri javob",
     "vocab", 100, "book", "emerald"),
    ("vocab_500",   "500 ta to'g'ri javob", "Lug'at mashqlarida 500 ta to'g'ri javob",
     "vocab", 500, "book", "teal"),
    ("vocab_1000",  "1000 ta to'g'ri javob", "Lug'at mashqlarida 1000 ta to'g'ri javob",
     "vocab", 1000, "book", "violet"),

    ("gram_1",      "Birinchi mavzu", "1 ta grammatika mavzusi yopildi",
     "grammar_topics", 1, "check", "sky"),
    ("gram_10",     "O'n mavzu", "10 ta grammatika mavzusi yopildi",
     "grammar_topics", 10, "check", "violet"),

    ("xp_500",      "500 XP", "500 XP to'pladingiz",
     "xp", 500, "star", "amber"),
    ("xp_2500",     "2 500 XP", "Jiddiy yo'l bosdingiz",
     "xp", 2500, "star", "violet"),
    ("xp_5000",     "5 000 XP", "Markaz yulduzi",
     "xp", 5000, "star", "rose"),

    ("lesson_30",   "30 dars", "30 ta darsga qatnashdingiz",
     "lessons", 30, "calendar", "sky"),
    ("lesson_100",  "100 dars", "100 ta darsga qatnashdingiz",
     "lessons", 100, "calendar", "emerald"),

    ("exam_1",      "Birinchi imtihon", "Birinchi imtihonni topshirdingiz",
     "exams", 1, "award", "teal"),
    ("exam_5",      "Besh imtihon", "5 ta imtihon natijasi bor",
     "exams", 5, "award", "amber"),
]

# Streak sovrinlari — necha kun uzluksiz mashqqa qancha coin.
# 2026-08-21 (Jahongir): "Streak sovrinlari — 7 kun -> 1, 14 kun -> 3,
# 30 kun -> 5. 60 kun 10, 100 kunga 20, 200 kunga 50, 365 kunga 100.
# avtomat bersin". Endi AVTOMAT beriladi (student_app'da, har zanjir
# uchun har bosqich bir marta).
STREAK_REWARDS = [(7, 1), (14, 3), (30, 5), (60, 10),
                  (100, 20), (200, 50), (365, 100)]

# Haftalik reyting sovrini. 2026-08-21 (Jahongir): "Haftalik reytingda
# 1-sentabrdan boshlab avtomat yutganga 10 coin berilsin" — endi hafta
# tugagach umumiy reyting g'olibiga AVTOMAT yoziladi (student_app).
RANK_PRIZE_COIN = 10

# Sovg'ani kim beradi
REWARD_GIVE = FULL_ACCESS + [ACADEMIC_HEAD, SALES_MANAGER, ADMINISTRATOR,
                             SUPPORT_TEACHER, HEAD_SUPPORT]


# =====================================================================
#  GAMIFICATION: XP, LEVEL, LIGA, SEASON
#
#  Coin va XP bir xil narsa emas:
#    COIN — sarflanadigan ichki valuta, kamayishi mumkin.
#    XP   — o'quvchining mehnati va intizomi. Sarflanmaydi, jarima
#           uchun kamaytirilmaydi. Faqat xato yozuv reversal orqali
#           qaytariladi.
#
#  Bu yerdagi ro'yxatlar faqat BOSHLANG'ICH holat: bir marta bazaga
#  tushadi, keyin admin panelidan boshqariladi.
# =====================================================================
XP_CATEGORIES = [
    ("academic", "Akademik", "sky"),
    ("attendance", "Davomat", "emerald"),
    ("activity", "Faollik", "amber"),
    ("consistency", "Muntazamlik", "violet"),
    ("community", "Jamoa", "teal"),
    ("achievement", "Yutuqlar", "rose"),
]
XP_CATEGORY_LABELS = {k: lbl for k, lbl, _ in XP_CATEGORIES}
XP_CATEGORY_TONE = {k: t for k, _, t in XP_CATEGORIES}

# ---- Ligalar --------------------------------------------------------
# rank, kalit, nom, min XP, max XP (None = cheklanmagan), rang,
# ikonka, mukofot coin
# Coin shkalasi 2026-08-20 da Jahongir bergan tartibda yangilandi:
# "1,2,3,4,5,6,8,10,12,14,16,18,20,25,30". Liga 14 ta, ko'tarilish
# esa 13 ta (Newcomer - boshlanish nuqtasi, unga ko'tarilib
# bo'lmaydi), shuning uchun 18 va 20 tushirib qoldirilib, cho'qqidagi
# ikki ligaga eng katta qiymatlar (25, 30) berildi. Eski shkala
# (jami 413 coin) juda saxiy edi - coin qadrsizlanardi; yangisi
# jami 136 coin (2026-08-25 da test bilan qayta sanaldi - izohda
# 126 deb yozilgan ekan, xato edi).
XP_LEAGUES = [
    (1, "newcomer", "Newcomer", 0, 99, "#f1f5f9", "🌱", 0),
    (2, "amateur", "Amateur", 100, 199, "#d4d4d8", "🔰", 1),
    (3, "wood", "Wood", 200, 399, "#a8a29e", "🪵", 2),
    (4, "stone", "Stone", 400, 599, "#78716c", "🪨", 3),
    (5, "bronze", "Bronze", 600, 999, "#d97706", "🥉", 4),
    (6, "silver", "Silver", 1000, 1499, "#94a3b8", "🥈", 5),
    (7, "gold", "Gold", 1500, 1999, "#f59e0b", "🥇", 6),
    (8, "crystal", "Crystal", 2000, 2999, "#8b5cf6", "💎", 8),
    (9, "elite", "Elite", 3000, 4999, "#ef4444", "⚔️", 10),
    (10, "master", "Master", 5000, 7999, "#22c55e", "🎓", 12),
    (11, "titan", "Titan", 8000, 11999, "#0ea5e9", "🗿", 14),
    (12, "champion", "Champion", 12000, 19999, "#eab308", "🏆", 16),
    (13, "legendary", "Legendary", 20000, 49999, "#991b1b", "🔥", 25),
    (14, "goat", "G.O.A.T", 50000, None, "#0f172a", "🐐", 30),
]
LEAGUE_LABELS = {k: lbl for _r, k, lbl, _a, _b, _c, _i, _co in XP_LEAGUES}

# Level = floor(Lifetime XP / XP_PER_LEVEL) + 1
XP_PER_LEVEL = 200   # 2026-08-21, Jahongir: "juda kam bolib qolgan 2x ga oshir"


def level_for(xp: float) -> int:
    return int(max(0, xp) // XP_PER_LEVEL) + 1


def level_progress(xp: float) -> dict:
    """Joriy levelning ichidagi progress va keyingi levelgacha qolgan XP."""
    xp = max(0, xp)
    lvl = level_for(xp)
    into = xp - (lvl - 1) * XP_PER_LEVEL
    return {
        "level": lvl,
        "into_level": round(into, 1),
        "need": XP_PER_LEVEL,
        "to_next": round(XP_PER_LEVEL - into, 1),
        "percent": round(into / XP_PER_LEVEL * 100, 1),
    }


# ---- Manba turlari --------------------------------------------------
XP_SOURCE_TYPES = [
    ("lesson", "Dars"),
    ("exam", "Imtihon"),
    ("homework", "Uyga vazifa"),
    ("certificate", "Sertifikat"),
    ("competition", "Musobaqa"),
    ("event", "Tadbir"),
    ("streak", "Streak"),
    ("manual", "Qo'lda"),
    ("system", "Tizim"),
    ("reversal", "Bekor qilish"),
]
XP_SOURCE_LABELS = dict(XP_SOURCE_TYPES)

XP_MODES = [("automatic", "Avtomat"), ("manual", "Qo'lda")]

# ---- Qoidalar katalogi ---------------------------------------------
# event_code, nom, kategoriya, XP, coin, dars/kun/hafta/oy chegarasi,
# rejim, tasdiq kerakmi
XP_RULES = [
    # --- Dars va davomat ---
    ("LESSON_PRESENT", "Darsga qatnashdi", "attendance", 10, 0,
     1, None, None, None, "automatic", False),
    ("LESSON_ON_TIME", "Darsga vaqtida keldi", "attendance", 2, 0,
     1, None, None, None, "automatic", False),
    # --- Uyga vazifa ---
    ("HOMEWORK_COMPLETE", "Uyga vazifa to'liq bajarildi", "academic", 8, 0,
     1, None, None, None, "automatic", False),
    ("HOMEWORK_PARTIAL", "Uyga vazifa qisman bajarildi", "academic", 3, 0,
     1, None, None, None, "automatic", False),
    ("HOMEWORK_EXCELLENT", "Uyga vazifa juda sifatli", "academic", 3, 0,
     1, None, None, None, "manual", False),
    # --- Darsda faollik ---
    ("ACTIVE_PARTICIPATION", "Darsda faol qatnashdi", "activity", 3, 0,
     1, None, None, None, "manual", False),
    ("CLASS_CHALLENGE_WINNER", "Dars challenge g'olibi", "activity", 5, 0,
     1, None, None, None, "manual", False),
    ("HELPED_CLASSMATE", "Boshqa o'quvchiga yordam berdi", "community", 2, 0,
     1, None, 2, None, "manual", False),
    ("PRESENTATION_COMPLETED", "Presentation yoki loyiha topshirdi",
     "activity", 10, 0, 1, None, None, None, "manual", False),
    # --- Haftalik test ---
    ("WEEKLY_TEST_60_69", "Test natijasi 60-69%", "academic", 5, 0,
     None, None, None, None, "automatic", False),
    ("WEEKLY_TEST_70_79", "Test natijasi 70-79%", "academic", 10, 0,
     None, None, None, None, "automatic", False),
    ("WEEKLY_TEST_80_89", "Test natijasi 80-89%", "academic", 20, 0,
     None, None, None, None, "automatic", False),
    ("WEEKLY_TEST_90_100", "Test natijasi 90-100%", "academic", 30, 0,
     None, None, None, None, "automatic", False),
    # --- O'sish ---
    ("WEEKLY_MOST_IMPROVED", "Haftaning eng ko'p o'sgan o'quvchisi",
     "academic", 20, 0, None, None, 1, None, "automatic", False),
    ("MONTHLY_MOST_IMPROVED", "Oyning eng ko'p o'sgan o'quvchisi",
     "academic", 60, 0, None, None, None, 1, "automatic", False),
    ("TEST_IMPROVEMENT_SMALL", "Testda 5-9% o'sish", "academic", 5, 0,
     None, None, None, None, "automatic", False),
    ("TEST_IMPROVEMENT_MEDIUM", "Testda 10-19% o'sish", "academic", 15, 0,
     None, None, None, None, "automatic", False),
    ("TEST_IMPROVEMENT_HIGH", "Testda 20%+ o'sish", "academic", 30, 0,
     None, None, None, None, "automatic", False),
    # --- Davomiylik ---
    ("FULL_ATTENDANCE_WEEK", "Hafta davomida barcha darslarda",
     "consistency", 20, 0, None, None, 1, None, "automatic", False),
    ("PERFECT_ATTENDANCE_MONTH", "Oy davomida sababsiz qoldirmadi",
     "consistency", 50, 0, None, None, None, 1, "automatic", False),
    ("HOMEWORK_FULL_WEEK", "Hafta davomida barcha uyga vazifalar",
     "consistency", 15, 0, None, None, 1, None, "automatic", False),
    ("CONSISTENT_STUDENT_MONTH", "Oyda davomat va homework 90%+",
     "consistency", 50, 0, None, None, None, 1, "automatic", False),
    # --- Streak ---
    ("ATTENDANCE_STREAK_5", "Ketma-ket 5 ta dars", "consistency", 15, 0,
     None, None, None, None, "automatic", False),
    ("ATTENDANCE_STREAK_10", "Ketma-ket 10 ta dars", "consistency", 30, 0,
     None, None, None, None, "automatic", False),
    ("ATTENDANCE_STREAK_20", "Ketma-ket 20 ta dars", "consistency", 75, 0,
     None, None, None, None, "automatic", False),
    ("ATTENDANCE_STREAK_40", "Ketma-ket 40 ta dars", "consistency", 150, 0,
     None, None, None, None, "automatic", False),
    ("HOMEWORK_STREAK_5", "Ketma-ket 5 ta homework", "consistency", 15, 0,
     None, None, None, None, "automatic", False),
    ("HOMEWORK_STREAK_10", "Ketma-ket 10 ta homework", "consistency", 30, 0,
     None, None, None, None, "automatic", False),
    ("HOMEWORK_STREAK_20", "Ketma-ket 20 ta homework", "consistency", 75, 0,
     None, None, None, None, "automatic", False),
    # --- Kurs progressi ---
    ("UNIT_COMPLETED", "Unit tugatildi", "academic", 25, 0,
     None, None, None, None, "automatic", False),
    ("MODULE_COMPLETED", "Modul tugatildi", "academic", 50, 0,
     None, None, None, None, "automatic", False),
    ("LEVEL_COMPLETED", "Til darajasi tugatildi", "academic", 150, 0,
     None, None, None, None, "automatic", False),
    ("INTERNAL_EXAM_PASSED", "Ichki yakuniy imtihondan o'tdi",
     "academic", 80, 0, None, None, None, None, "automatic", False),
    ("INTERNAL_EXAM_EXCELLENT", "Ichki imtihondan 90%+", "academic", 50, 0,
     None, None, None, None, "automatic", False),
    # --- Mock ---
    ("MOCK_EXAM_PARTICIPATION", "Mock examda qatnashdi", "academic", 10, 0,
     None, None, None, None, "automatic", False),
    ("MOCK_EXAM_GOOD_RESULT", "Mock natijasi minimumdan yuqori",
     "academic", 30, 0, None, None, None, None, "automatic", False),
    ("MOCK_EXAM_IMPROVEMENT", "Mock natijasida sezilarli o'sish",
     "academic", 50, 0, None, None, None, None, "automatic", False),
    ("MOCK_EXAM_TOP_1", "Mock bo'yicha 1-o'rin", "achievement", 100, 0,
     None, None, None, None, "automatic", False),
    ("MOCK_EXAM_TOP_2", "Mock bo'yicha 2-o'rin", "achievement", 70, 0,
     None, None, None, None, "automatic", False),
    ("MOCK_EXAM_TOP_3", "Mock bo'yicha 3-o'rin", "achievement", 50, 0,
     None, None, None, None, "automatic", False),
    # --- CEFR ---
    ("CEFR_A2", "CEFR A2", "achievement", 150, 0,
     None, None, None, None, "manual", True),
    ("CEFR_B1", "CEFR B1", "achievement", 250, 0,
     None, None, None, None, "manual", True),
    ("CEFR_B2", "CEFR B2", "achievement", 400, 0,
     None, None, None, None, "manual", True),
    ("CEFR_C1", "CEFR C1", "achievement", 600, 0,
     None, None, None, None, "manual", True),
    # --- IELTS ---
    ("IELTS_5_0", "IELTS 5.0", "achievement", 150, 0,
     None, None, None, None, "manual", True),
    ("IELTS_5_5", "IELTS 5.5", "achievement", 250, 0,
     None, None, None, None, "manual", True),
    ("IELTS_6_0", "IELTS 6.0", "achievement", 350, 0,
     None, None, None, None, "manual", True),
    ("IELTS_6_5", "IELTS 6.5", "achievement", 500, 0,
     None, None, None, None, "manual", True),
    ("IELTS_7_0", "IELTS 7.0", "achievement", 700, 0,
     None, None, None, None, "manual", True),
    ("IELTS_7_5", "IELTS 7.5", "achievement", 900, 0,
     None, None, None, None, "manual", True),
    ("IELTS_8_0_PLUS", "IELTS 8.0+", "achievement", 1200, 0,
     None, None, None, None, "manual", True),
    # --- Musobaqa ---
    ("BRANCH_COMPETITION_WINNER", "Filial musobaqasi g'olibi",
     "achievement", 50, 0, None, None, None, None, "manual", False),
    ("CITY_COMPETITION_WINNER", "Shahar musobaqasi g'olibi",
     "achievement", 100, 0, None, None, None, None, "manual", False),
    ("REGIONAL_COMPETITION_WINNER", "Viloyat musobaqasi g'olibi",
     "achievement", 200, 0, None, None, None, None, "manual", True),
    ("NATIONAL_COMPETITION_WINNER", "Respublika musobaqasi g'olibi",
     "achievement", 500, 0, None, None, None, None, "manual", True),
    ("INTERNATIONAL_COMPETITION_WINNER", "Xalqaro musobaqa g'olibi",
     "achievement", 1000, 0, None, None, None, None, "manual", True),
    # --- Tadbir va jamoa ---
    ("EVENT_PARTICIPATION", "Tadbirda qatnashdi", "community", 5, 0,
     None, None, None, None, "manual", False),
    ("EVENT_VOLUNTEER", "Tadbirda volontyor bo'ldi", "community", 20, 0,
     None, None, None, None, "manual", False),
    ("TEAM_PROJECT_COMPLETED", "Jamoaviy loyihani tugatdi",
     "community", 15, 0, None, None, None, None, "manual", False),
]

# Test natijasidan XP: faqat BITTA qoida ishlaydi (eng yuqorisi)
TEST_XP_BANDS = [
    (90, "WEEKLY_TEST_90_100"),
    (80, "WEEKLY_TEST_80_89"),
    (70, "WEEKLY_TEST_70_79"),
    (60, "WEEKLY_TEST_60_69"),
]
# O'sish bonusi: ham faqat bittasi
TEST_IMPROVEMENT_BANDS = [
    (20, "TEST_IMPROVEMENT_HIGH"),
    (10, "TEST_IMPROVEMENT_MEDIUM"),
    (5, "TEST_IMPROVEMENT_SMALL"),
]
# Streak milestone: bosqichga yetganda bir marta
ATTENDANCE_STREAKS = [(40, "ATTENDANCE_STREAK_40"), (20, "ATTENDANCE_STREAK_20"),
                      (10, "ATTENDANCE_STREAK_10"), (5, "ATTENDANCE_STREAK_5")]
HOMEWORK_STREAKS = [(20, "HOMEWORK_STREAK_20"), (10, "HOMEWORK_STREAK_10"),
                    (5, "HOMEWORK_STREAK_5")]

# Sertifikat XP: yangi natija olinganda faqat FARQI beriladi
CERT_RULES = {
    "cefr": ["CEFR_A2", "CEFR_B1", "CEFR_B2", "CEFR_C1"],
    "ielts": ["IELTS_5_0", "IELTS_5_5", "IELTS_6_0", "IELTS_6_5",
              "IELTS_7_0", "IELTS_7_5", "IELTS_8_0_PLUS"],
}
CERT_MODE_DIFF = "diff"       # default: faqat farqi
CERT_MODE_FULL = "full"

# Musobaqada o'rin bo'yicha koeffitsiyent
PLACE_MULTIPLIER = {1: 1.0, 2: 0.75, 3: 0.5}

# ---- Ustoz chegaralari ---------------------------------------------
TEACHER_XP_PER_WEEK = 20      # bitta o'quvchiga haftasiga
TEACHER_XP_PER_LESSON = 10    # bitta darsda
APPROVAL_ABOVE_XP = 100       # bundan katta qo'lda XP tasdiq talab qiladi

# Ustoz qaysi qoidalardan XP bera oladi (Quick XP tugmalari)
TEACHER_QUICK_XP = [
    "ACTIVE_PARTICIPATION", "HOMEWORK_EXCELLENT",
    "CLASS_CHALLENGE_WINNER", "HELPED_CLASSMATE",
    "PRESENTATION_COMPLETED",
]

# ---- Streaklar ------------------------------------------------------
STREAK_KINDS = [
    ("attendance", "Davomat streak", "emerald"),
    ("homework", "Homework streak", "sky"),
    ("test", "Test streak", "violet"),
]
STREAK_LABELS = {k: lbl for k, lbl, _ in STREAK_KINDS}
STREAK_TONE = {k: t for k, _, t in STREAK_KINDS}

# ---- Fraud ----------------------------------------------------------
FRAUD_TYPES = [
    ("teacher_spike", "Ustoz odatdagidan ko'p XP berdi", "MEDIUM"),
    ("daily_limit", "O'quvchi kunlik chegaradan oshdi", "MEDIUM"),
    ("duplicate", "Takroriy tranzaksiya urinishi", "LOW"),
    ("big_manual", "Katta XP hujjatsiz berildi", "HIGH"),
    ("mass_award", "Qisqa vaqtda ko'p o'quvchiga katta XP", "HIGH"),
    ("inactive_student", "Faol bo'lmagan o'quvchiga XP", "MEDIUM"),
    ("no_lesson", "Dars bo'lmagan kunda dars XP'si", "MEDIUM"),
    ("foreign_group", "O'ziga biriktirilmagan guruhga XP", "HIGH"),
    ("cert_reuse", "Sertifikat raqami qayta ishlatildi", "CRITICAL"),
    ("many_reversals", "Ko'p marta bekor qilingan", "HIGH"),
]
FRAUD_LABELS = {k: lbl for k, lbl, _ in FRAUD_TYPES}
FRAUD_SEVERITY = {k: s for k, _, s in FRAUD_TYPES}
FRAUD_TONE = {"LOW": "slate", "MEDIUM": "amber", "HIGH": "orange",
              "CRITICAL": "red"}
FRAUD_STATUSES = [("open", "Ochiq"), ("reviewed", "Ko'rildi"),
                  ("dismissed", "Rad etildi")]

# Ustozning manual XP'si o'rtachasidan necha barobar oshsa - signal
TEACHER_SPIKE_FACTOR = 3.0
MASS_AWARD_MINUTES = 5
MASS_AWARD_STUDENTS = 10

# ---- Leaderboard ----------------------------------------------------
LEADERBOARD_SCOPES = [
    ("lifetime", "Umumiy XP"),
    ("season", "Mavsum XP"),
    ("week", "Haftalik"),
    ("month", "Oylik"),
]
LEADERBOARD_LABELS = dict(LEADERBOARD_SCOPES)

# ---- Ruxsatlar ------------------------------------------------------
XP_AWARD = FULL_ACCESS + [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER,
                          HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER]
XP_ADMIN = FULL_ACCESS + [ACADEMIC_HEAD]
XP_VIEW = FULL_ACCESS + [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER,
                         HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER,
                         ADMINISTRATOR, BRANCH_MANAGER, SALES_MANAGER]


# =====================================================================
#  DARS BAHOLASH MEZONLARI
#
#  Ikkita jadval: birinchi darsni o'tish va asosiy darsni o'tish.
#  Ikkalasi ham 100 balldan. Nomzod ishga olinayotganda ham, ishlayotgan
#  ustoz tekshirilganda ham shu mezon ishlatiladi.
#
#  Bu ro'yxat faqat BOSHLANG'ICH holat: bir marta bazaga tushadi,
#  keyin HR bo'limidan tahrirlanadi.
# =====================================================================
RUBRIC_FIRST = "first_lesson"
RUBRIC_MAIN = "main_lesson"

RUBRICS = [
    (RUBRIC_FIRST, "Birinchi darsni o'tish metodikasi",
     "Yangi guruhdagi birinchi dars: tanishuv, qoidalar, ishonch"),
    (RUBRIC_MAIN, "Asosiy darsni o'tish mezoni",
     "Kundalik dars: reja, tushuntirish, faollik, yakun"),
]
RUBRIC_LABELS = {k: lbl for k, lbl, _ in RUBRICS}

# (tartib raqami, mezon, ball)
RUBRIC_MAIN_ITEMS = [
    (1, "S.M.A.R.T dars reja asosida darsga kirish", 7),
    (2, "BLOOM strategiyasi bilan darsga kirish", 5),
    (3, "Kirish (oldingi mavzularga bog'lagan holda)", 2),
    (4, "Tarqatma materialdan foydalangan holda o'tish", 2),
    (5, "20 daqiqada har bir o'quvchining uyga vazifalarini tekshira olish "
        "(kombinatsiyalar orqali) (online/offline)", 7),
    (6, "Yangi mavzu nomini o'quvchilarning o'zlariga ayttirish", 2),
    (7, "Yangi mavzuni savol bilan boshlash (e'tiborni tortish uchun)", 2),
    (8, "Ustoz 90% savol, 10% darak gapdan foydalanishi", 8),
    (9, "Darsda o'quvchining ingliz tili bo'yicha mindsetini shakllantirish", 2),
    (10, "Ko'z qarash", 1),
    (11, "Qo'l harakatlari", 1),
    (12, "Ovoz toni o'zgaruvchan bo'lishi", 2),
    (13, "Tezlik o'zgaruvchan bo'lishi", 2),
    (14, "O'tilgan mavzuga amaliy mashg'ulotlar", 3),
    (15, "O'quvchilarni ustozdan avval yangi \"detallarni\" aytishlari va "
         "yozishlariga undash", 3),
    (16, "Orqaga o'girilmaslik", 2),
    (17, "Yangi mavzuni 15 daqiqada tushuntira olish", 8),
    (18, "O'quvchi savol berganda — savollar berish orqali javobni "
         "o'quvchining o'ziga topib ayttirish (tarqatma materiallardan "
         "foydalangan holda)", 5),
    (19, "Warm-up, ice breaker va energizerlardan foydalanish", 3),
    (20, "Har bir o'quvchi e'tiborda bo'lishi, darsda hamma qatnashishi", 3),
    (21, "Mavzuni 5 yoshlik bola tushunadigan tilda tushuntirish", 3),
    (22, "Har darsda oldingi mavzularni takrorlab chiqish "
         "(kombinatsiya shaklida)", 7),
    (23, "Tarqatma materiallar har bitta o'quvchida bo'lishini ta'minlash", 1),
    (24, "Sense of humor'ni darsda yetarli miqdorda ishlatish", 2),
    (25, "Darsni qiziqarli o'tish, mavzuni qiziqarli tushuntirish", 5),
    (26, "O'quvchilar uyga vazifani tushunganini isbotlashi uchun "
         "qayta so'rash", 2),
    (27, "Jahl chiqmasdan qattiqqo'l bo'lish", 1),
    (28, "Gamifikatsiyadan foydalanish", 5),
    (29, "O'quvchining kichik yutuqlarini maqtash", 2),
    (30, "Dars yakunida darsni umumlashtirish va xulosalash", 2),
]

RUBRIC_FIRST_ITEMS = [
    (1, "Professional tashqi ko'rinish", 2),
    (2, "Qiyofadagi sokinlik, samimiylik, ochiqlik", 2),
    (3, "Tanishuv: ism/familiya", 2),
    (4, "Tanishuv: faoliyati, malakasi", 2),
    (5, "Tanishuv: nega ular sizda o'qishi kerak "
        "(competitive advantage)", 2),
    (6, "Munosabat taklif qilish", 2),
    (7, "O'quvchi bilan minimum 2-3 daqiqa suhbatlashish", 7),
    (8, "Har bir o'quvchiga karta ochib to'ldirish (obsidian)", 7),
    (9, "Bilim darajalarini aniqlab olish", 2),
    (10, "Oldin borgan o'quvchilarni Chaos'ga tashlash", 5),
    (11, "O'quvchilar bir-biri bilan tanishib tezda chiqishib ketishini "
         "ta'minlash", 5),
    (12, "Darsdagi tartib-qoidalarni hammasiga tuzdirish", 8),
    (13, "Yangi mavzuni savol bilan boshlash (e'tiborni tortish uchun)", 2),
    (14, "Ekspertligingizni ko'rsatib qo'yish — fan bo'yicha tushuncha "
         "berish orqali", 5),
    (15, "Nega sizning faningizni o'qishi kerakligini anglatish", 5),
    (16, "Shu fanni o'rganishdan maqsad va kelajakdagi rejalari haqida "
         "commitment letter yozdirish", 5),
    (17, "Fanga kirishda eng sodda, eng atom darajadagi oson narsani "
         "o'rgatish", 5),
    (18, "\"O'rgandim\" degan narsani his qildirish", 5),
    (19, "Telegram guruh ochish", 2),
    (20, "Darsda o'quvchiga kerak bo'ladigan applarni o'rnatgizish, hamma "
         "ishlatganini ko'rish", 5),
    (21, "Har bir o'quvchi e'tiborda bo'lishi, darsda hamma qatnashishi", 3),
    (22, "Guruhga umumiy nom berish", 2),
    (23, "O'quvchiga ishonch berish", 3),
    (24, "Sense of humor'ni darsda yetarli miqdorda ishlatish", 2),
    (25, "O'quvchilar uyga vazifani tushunganini isbotlashi uchun "
         "qayta so'rash", 2),
    (26, "Darsdan keyin o'zingiz haqingizda to'liq ma'lumotni guruhga "
         "joylash", 2),
    (27, "Har bir o'quvchiga kamida 1 marta shaxsan murojaat qilish", 2),
    (28, "O'quvchining kichik yutuqlarini maqtash", 2),
    (29, "Dars yakunida darsni umumlashtirish va xulosalash", 2),
]

RUBRIC_ITEMS = {
    RUBRIC_MAIN: RUBRIC_MAIN_ITEMS,
    RUBRIC_FIRST: RUBRIC_FIRST_ITEMS,
}

# Baholanuvchi kim: nomzod yoki ishlayotgan ustoz
OBSERVATION_TARGETS = [("candidate", "Nomzod"), ("teacher", "Ustoz")]

# Nomzodni sinash bosqichlari.
#
# Mantiq shunday: avval nomzod O'Z HOLICHA dars beradi — bu uning
# boshlang'ich darajasi. Keyin unga mezonlar tushuntiriladi va u
# QAYTA baholanadi. Ikkinchi natija emas, IKKALASI ORASIDAGI FARQ
# eng muhim signal: odam aytilganini qabul qilib o'zgara oladimi?
# Sust boshlab keskin o'sgan odam, yaxshi boshlab qimirlamagandan
# ko'ra ko'proq narsa va'da qiladi.
OBSERVATION_STAGES = [
    ("before", "1-baholash: o'z holicha", "slate"),
    ("coached", "2-baholash: tushuntirilgandan keyin", "sky"),
    ("extra", "Qo'shimcha baholash", "violet"),
]
STAGE_LABELS = {k: lbl for k, lbl, _ in OBSERVATION_STAGES}
STAGE_TONE = {k: t for k, _, t in OBSERVATION_STAGES}

# O'sish qanchalik yaxshi ekanini baholash (foiz punktida)
def growth_band(delta: float) -> tuple:
    """O'sishdan xulosa: (matn, rang, tavsiya)."""
    if delta >= 20:
        return ("Juda tez o'rganadi", "emerald",
                "Aytilganini darrov qabul qildi — o'sish salohiyati yuqori")
    if delta >= 10:
        return ("Yaxshi o'sdi", "teal",
                "Fikrni qabul qiladi, o'rgatsa bo'ladi")
    if delta >= 3:
        return ("Sal o'sdi", "amber",
                "O'zgarish bor, lekin sekin — ko'proq mashq kerak")
    if delta > -3:
        return ("O'zgarmadi", "orange",
                "Tushuntirilgandan keyin ham o'zgarmadi — bu jiddiy signal")
    return ("Pastladi", "red",
            "Ikkinchi urinishda yomonlashdi — bosim ostida ishlay oladimi?")

# Natija darajalari — rangi va xulosasi
def rubric_band(percent: float) -> tuple:
    """Foizdan xulosa: (kalit, matn, rang)."""
    if percent >= 85:
        return ("excellent", "A'lo", "emerald")
    if percent >= 70:
        return ("good", "Yaxshi", "teal")
    if percent >= TEACHER_MIN_SKILL:
        return ("pass", "O'tdi", "amber")
    return ("fail", "Yetarli emas", "red")


OBSERVATION_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, HR_MANAGER,
                                    BRANCH_MANAGER, HEAD_EXAMINER]

# Daraja ko'tarilishi qachon kuchga kiradi. Ustoz oy o'rtasida hamma
# reglamentni bajarsa ham, yangi daraja KEYINGI OYNING 1-sanasidan
# boshlanadi: shunda oy bitta stavkada yopiladi va oylik chalkashmaydi.
GRADE_EFFECTIVE_NEXT_MONTH = True


# =====================================================================
#  O'QUV MARKAZ TO'LGANLIGI (fill)
#
#  Asoschi uchun eng muhim raqamlardan biri: markaz o'z sig'imining
#  necha foizini ishlatyapti.
#
#  Hisob mantiqi:
#    Bitta xonaga TOQ kunlari (du/chor/ju) 2 ta guruh, JUFT kunlari
#    (se/pay/sha) 2 ta guruh sig'adi — jami 4 ta guruh.
#    Xona sig'imi 25 kishi bo'lsa: 4 x 25 = 100 o'quvchi.
#    Hamma xonalar shunday qo'shilib, markazning sig'imi chiqadi.
#
#  4 ta guruh — O'RTACHA holat. Zo'r ishlaganda 5 ta, ajoyib
#  ishlaganda 6 ta guruh sig'diriladi.
# =====================================================================
FILL_LEVELS = [
    ("normal", "O'rtacha", 4, "Toq kunlari 2 + juft kunlari 2 guruh"),
    ("good", "Zo'r", 5, "Bitta xonaga 5 ta guruh"),
    ("great", "Ajoyib", 6, "Bitta xonaga 6 ta guruh"),
]
FILL_LEVEL_LABELS = {k: lbl for k, lbl, _g, _d in FILL_LEVELS}
FILL_GROUPS = {k: g for k, _lbl, g, _d in FILL_LEVELS}
FILL_DEFAULT_LEVEL = "normal"

# Xona sig'imi kiritilmagan bo'lsa shu ishlatiladi
DEFAULT_ROOM_SEATS = 25

# Toq va juft kunlar
ODD_DAYS = ["mon", "wed", "fri"]
EVEN_DAYS = ["tue", "thu", "sat"]


def day_side(days) -> str:
    """Guruh toq kunlarimi, juft kunlarimi yoki aralashmi."""
    ds = set(days or [])
    if not ds:
        return "unknown"
    odd = bool(ds & set(ODD_DAYS))
    even = bool(ds & set(EVEN_DAYS))
    if odd and even:
        return "mixed"
    return "odd" if odd else "even" if even else "unknown"


def fill_grade(percent: float) -> tuple:
    """To'lganlik foizidan xulosa: (matn, rang)."""
    if percent >= 90:
        return ("To'lgan", "emerald")
    if percent >= 70:
        return ("Yaxshi", "teal")
    if percent >= 50:
        return ("O'rtacha", "amber")
    if percent >= 30:
        return ("Bo'sh", "orange")
    return ("Juda bo'sh", "red")


FILL_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, BRANCH_MANAGER,
                             FINANCE_DIRECTOR, SALES_HEAD, SALES_MANAGER]


# =====================================================================
#  SMM: KONTENT QUVURI
#
#  SMM bo'limi post ishlab chiqaradigan bo'lim emas — e'tibor, ishonch,
#  murojaat va sotuv yaratadigan bo'lim. Shuning uchun har bir kontent
#  g'oyadan natijagacha bitta quvurdan o'tadi:
#
#    G'oya -> brief -> ssenariy -> ishlab chiqarish -> montaj ->
#    SMM tekshiruvi -> tasdiq -> rejalashtirildi -> joylandi ->
#    natija o'lchanmoqda -> yakunlandi
# =====================================================================
CONTENT_STATUSES = [
    ("idea", "G'oya", "slate"),
    ("script", "Ssenariy tayyorlanmoqda", "sky"),
    ("shooting", "Tasvirga olinmoqda", "violet"),
    ("editing", "Montaj / dizayn", "amber"),
    ("review", "SMM tekshiruvi", "amber"),
    ("approval", "Tasdiq kutilmoqda", "orange"),
    ("ready", "Tayyor / rejalashtirilgan", "emerald"),
    ("published", "Joylandi", "slate900"),
    ("measuring", "Natija o'lchanmoqda", "teal"),
    ("done", "Yakunlandi", "teal"),
    ("late", "Kechikdi", "red"),
    ("rework", "Qayta ishlashga qaytarildi", "brown"),
    ("cancelled", "Bekor qilindi", "slate"),
]
CONTENT_STATUS_LABELS = {k: lbl for k, lbl, _ in CONTENT_STATUSES}
CONTENT_STATUS_TONE = {k: t for k, _, t in CONTENT_STATUSES}
# Quvurning tabiiy tartibi (kechikdi/bekor bundan tashqarida)
CONTENT_FLOW = ["idea", "script", "shooting", "editing", "review",
                "approval", "ready", "published", "measuring", "done"]
CONTENT_OPEN = ["idea", "script", "shooting", "editing", "review",
                "approval", "ready", "rework"]
CONTENT_LIVE = ["published", "measuring", "done"]

CONTENT_PLATFORMS = [
    ("ig_post", "Instagram post", "rose"),
    ("ig_reels", "Instagram Reels", "rose"),
    ("ig_story", "Instagram Story", "rose"),
    ("telegram", "Telegram post", "sky"),
    ("tiktok", "TikTok video", "slate"),
    ("yt_shorts", "YouTube Shorts", "red"),
    ("youtube", "YouTube video", "red"),
    ("facebook", "Facebook post", "sky"),
    ("website", "Sayt maqolasi", "teal"),
    ("broadcast", "SMS / Telegram broadcast", "amber"),
]
PLATFORM_LABELS = {k: lbl for k, lbl, _ in CONTENT_PLATFORMS}
PLATFORM_TONE = {k: t for k, _, t in CONTENT_PLATFORMS}

CONTENT_FORMATS = [
    ("reels", "Reels"), ("story", "Story"), ("carousel", "Carousel"),
    ("static", "Statik post"), ("long_video", "Uzun video"),
    ("short_video", "Qisqa video"), ("live", "Live"),
    ("testimonial", "Testimonial"), ("article", "Maqola"),
]
FORMAT_LABELS = dict(CONTENT_FORMATS)

# ---- Kontent maqsadi: majburiy ----
# "Shunchaki joylash" uchun kontent yaratilmaydi. Maqsad tanlanadi va
# natija AYNAN SHU maqsadga qarab o'lchanadi.
CONTENT_GOALS = [
    ("awareness", "Brand awareness", "reach"),
    ("trust", "Ishonch oshirish", "engagement"),
    ("lead", "Lead yig'ish", "leads"),
    ("sales", "Sotuv", "sales"),
    ("retention", "Retention", "engagement"),
    ("parents", "Ota-onalarni xabardor qilish", "reach"),
    ("result", "O'quvchi natijasini ko'rsatish", "engagement"),
    ("teacher", "Ustoz brendini rivojlantirish", "engagement"),
    ("event", "Tadbirga odam yig'ish", "leads"),
    ("vacancy", "Vakansiya", "leads"),
    ("community", "Community", "engagement"),
    ("objection", "Objection handling", "leads"),
    ("referral", "Referral", "leads"),
    ("reengage", "Re-engagement", "engagement"),
]
GOAL_LABELS = {k: lbl for k, lbl, _ in CONTENT_GOALS}
GOAL_METRIC = {k: m for k, _, m in CONTENT_GOALS}
GOAL_METRIC_LABELS = {
    "reach": "Reach va yangi auditoriya",
    "engagement": "Faol harakatlar",
    "leads": "Murojaat va sifatli lead",
    "sales": "Sotuv va tushum",
}

# ---- Kontent yo'nalishlari (pillars) ----
CONTENT_PILLARS = [
    ("results", "Student Results", "emerald",
     "IELTS, CEFR, TOPIK, olimpiada, progress, oldin va keyin"),
    ("teacher", "Teacher Branding", "violet",
     "Ustoz tanishtiruvi, metodi, dars jarayoni, natijalari"),
    ("education", "Educational Content", "sky",
     "Qoidalar, IELTS maslahat, so'zlar, xatolar, mini testlar"),
    ("trust", "Trust Content", "teal",
     "Ota-ona fikri, dars jarayoni, examiner nazorati, support"),
    ("sales", "Sales Content", "amber",
     "Yangi guruh, joylar soni, taklif, narxga qiymat, CTA"),
    ("life", "Jony Life", "rose",
     "Tadbirlar, Sunday events, Day X, coin va XP"),
    ("objection", "Objection Handling", "orange",
     "Narxi qimmat, vaqtim yo'q, natija qachon bo'ladi"),
    ("culture", "Brand Culture", "slate",
     "Tarix, qadriyat, jamoa, missiya, muhit"),
    # 2026-08-27: Jahongirning kontent-plan jadvalidagi yo'nalishlar.
    # Eskilari O'CHIRILMADI — ular bilan yozilgan kontent buzilmasin.
    ("env", "Muhit va jarayon", "cyan",
     "Koridor, tanaffus, dars jarayoni — JONY = MUHIT"),
    ("dayx", "DAY X", "amber",
     "Yillik poyga: Umra, iPhone, kompyuter"),
    ("useful", "Foydali ta'lim", "sky",
     "IELTS/CEFR maslahat, trap, so'z, mini-dars"),
    ("system", "Ta'lim tizimi", "indigo",
     "Daraja testi, unit-test, joylashuv, nazorat"),
    ("team", "Ustozlar va jamoa", "violet",
     "Ustoz-serial, metod, jamoa"),
    ("stories", "Natijalar va hikoyalar", "emerald",
     "O'quvchi natijasi va uning yo'li"),
    ("app", "Student App", "blue",
     "Rayonda yagona ilova — imkoniyatlari"),
    ("offer", "To'g'ridan-to'g'ri taklif", "rose",
     "Qabul, joy soni, muddat, narx"),
]
PILLAR_LABELS = {k: lbl for k, lbl, _t, _d in CONTENT_PILLARS}
PILLAR_TONE = {k: t for k, _l, t, _d in CONTENT_PILLARS}

# 2026-08-27: nomlar Jahongirning kontent-plan jadvalidagidek —
# "Tanilish / Ishonch / Qaror / Tavsiya". KALITLAR o'zgarmadi,
# shuning uchun eski kontent yozuvlari buzilmaydi.
FUNNEL_STAGES = [
    ("tofu", "Tanilish"),
    ("mofu", "Ishonch"),
    ("bofu", "Sotuv"),
    ("retention", "G'amxo'rlik"),
    # 2026-08-27: jadvalda alohida bosqich — o'quvchi do'stiga
    # tavsiya qiladigan kontent (referral tizimining asosi).
    ("advocacy", "Tavsiya"),
]
FUNNEL_LABELS = dict(FUNNEL_STAGES)


# =====================================================================
#  EXCEL KONTENT-PLANNI IMPORT QILISH XARITASI (2026-08-27)
#
#  Jahongir tayyor jadvalni yubordi va u O'ZBEKCHA so'zlar bilan
#  to'ldirilgan ("Muhit va jarayon", "Tanilish", "Reels-reportaj").
#  Tizim ichida esa kalitlar ishlatiladi. Shu xarita ikkalasini
#  bog'laydi.
#
#  QOIDA: xarita KENG bo'lsin. SMM keyingi oyda "Reels — reportaj"
#  deb yozib qo'ysa ham tanilishi kerak, aks holda import har oy
#  qo'lda tuzatishga aylanadi.
# =====================================================================
IMPORT_PILLARS = {
    "muhit va jarayon": "env", "muhit": "env", "jarayon": "env",
    "day x": "dayx", "dayx": "dayx",
    "foydali ta'lim": "useful", "foydali talim": "useful",
    "ta'lim tizimi": "system", "talim tizimi": "system",
    "ustozlar va jamoa": "team", "ustozlar": "team", "jamoa": "team",
    "natijalar va hikoyalar": "stories", "natijalar": "stories",
    "student app": "app", "app": "app", "ilova": "app",
    "muammolar va e'tirozlar": "objection", "e'tirozlar": "objection",
    "to'g'ridan-to'g'ri taklif": "offer", "taklif": "offer",
    "sotuv": "sales", "brend": "culture", "brand culture": "culture",
}
IMPORT_FUNNELS = {
    "tanilish": "tofu", "tanishtirish": "tofu",
    "ishonch": "mofu", "qiziqtirish": "mofu",
    "sotuv": "bofu", "qaror": "bofu",
    "g'amxo'rlik": "retention", "gamxorlik": "retention",
    "saqlab qolish": "retention",
    "tavsiya": "advocacy",
}
IMPORT_GOALS = {
    "qamrov": "awareness", "tanilish": "awareness",
    "ishonch": "trust",
    "muloqot": "community", "community": "community",
    "sotuv": "sales", "lead": "lead", "murojaat": "lead",
    "tadbir": "event", "referral": "referral",
}
IMPORT_FORMATS = [
    # (matnda shu bo'lsa, format shu bo'ladi) — tartib MUHIM:
    # avval aniqrog'i tekshiriladi.
    ("karusel", "carousel"), ("carousel", "carousel"),
    ("stories", "story"), ("story", "story"),
    ("intervyu", "testimonial"), ("testimonial", "testimonial"),
    ("live", "live"), ("efir", "live"),
    ("maqola", "article"), ("post", "static"),
    ("reels", "reels"),
    ("video", "long_video"),
]


def import_key(value, table, default=None):
    """O'zbekcha matndan tizim kalitini topadi."""
    t = str(value or "").strip().lower()
    if not t:
        return default
    if t in table:
        return table[t]
    for k, v in table.items():          # qismiy moslik
        if k in t:
            return v
    return default


def import_format(value, default="reels"):
    t = str(value or "").strip().lower()
    if not t:
        return default
    for needle, key in IMPORT_FORMATS:
        if needle in t:
            # "Video (15 daqiqa)" uzun video, "Reels-demo" — reels
            return key
    return default

# =====================================================================
#  SSENARIY SHABLONLARI (2026-08-27)
#
#  Jahongir: "ichiga ssearniysi scriptini yozadigan ham bo'lishi
#  kerak SMM manager kirib shuni kopya qilishga oson bo'lsin,
#  ozgartirishga oson bo'lsin."
#
#  Bo'sh oynaga qarab turish — kontentni sekinlashtiradigan asosiy
#  narsa. Shuning uchun formatga qarab TAYYOR SKELET beriladi:
#  SMM boshlaydi-yu, nolga qaramaydi. Skelet vaqt bilan bo'lingan,
#  chunki Reels'da 3 soniyada ushlamasang odam ketadi.
# =====================================================================
SCRIPT_TEMPLATES = {
    "reels": """[0-3 s] HOOK — ekranda katta yozuv, ovozda savol
{hook}

[3-8 s] MUAMMO — tomoshabin o'zini tanisin
...

[8-20 s] YECHIM — asosiy fikr
{message}

[20-35 s] DALIL — raqam, natija, sertifikat, jonli lavha
{proof}

[35-45 s] CTA — bitta aniq harakat
{cta}

--- SUR'AT ---
Kadr almashishi: har 2-3 soniyada
Ekrandagi yozuv: HOOK va CTA majburiy
Musiqa: trend, ovoz ustidan past
""",
    "carousel": """SLAYD 1 — HOOK (faqat shu o'qiladi, qolgani shunga bog'liq)
{hook}

SLAYD 2 — muammo
...

SLAYD 3-5 — yechim bosqichma-bosqich
{message}

SLAYD 6 — DALIL (raqam yoki natija)
{proof}

SLAYD 7 — CTA
{cta}

--- QOIDA ---
Har slaydda BITTA fikr. 2 qatordan oshmasin.
""",
    "story": """1-STORY — e'tibor (savol yoki kutilmagan kadr)
{hook}

2-STORY — mazmun
{message}

3-STORY — interaktiv stiker (so'rovnoma / savol / test)
...

4-STORY — CTA + havola
{cta}
""",
    "static": """RASMDAGI YOZUV (5 so'zdan oshmasin):
{hook}

MATN (caption):
1-jumla — ilgak: {hook}
2-3-jumla — asosiy fikr: {message}
4-jumla — dalil: {proof}
Oxirgi jumla — CTA: {cta}
""",
    "testimonial": """[0-5 s] KIM — ism, natija, bir jumlada
...

[5-15 s] OLDIN qanday edi
...

[15-30 s] NIMA O'ZGARDI — aniq raqam bilan
{proof}

[30-40 s] KIMGA TAVSIYA QILADI
{cta}

--- QOIDA ---
Yodlangan matn EMAS. Savol beriladi, javob tabiiy chiqadi.
""",
    "long_video": """[0-15 s] KIRISH — nima haqida va nega qolish kerak
{hook}

[15 s - 2 daq] 1-QISM
{message}

[2-4 daq] 2-QISM — dalil va misollar
{proof}

[4-5 daq] XULOSA + CTA
{cta}
""",
}
SCRIPT_DEFAULT = SCRIPT_TEMPLATES["reels"]


def script_template(fmt: str, **kw) -> str:
    """Formatga mos ssenariy skeleti. Brief maydonlari o'rniga
    qo'yiladi; bo'sh bo'lsa "..." qoladi."""
    tpl = SCRIPT_TEMPLATES.get(fmt or "", SCRIPT_DEFAULT)
    safe = {k: (str(v).strip() or "...") for k, v in kw.items()}
    for need in ("hook", "message", "proof", "cta"):
        safe.setdefault(need, "...")
    try:
        return tpl.format(**safe)
    except Exception:
        return tpl


# ---- Kim tasdiqlaydi ----
# Kontent turiga qarab tasdiqlovchi o'zi aniqlanadi — SMM kimga
# yuborishni o'ylab o'tirmaydi.
APPROVAL_BY_PILLAR = {
    "education": SMM_MANAGER,
    "life": SMM_MANAGER,
    "culture": SMM_MANAGER,
    "trust": SMM_MANAGER,
    "objection": SALES_HEAD,
    "sales": SALES_HEAD,
    "results": ACADEMIC_HEAD,
    "teacher": ACADEMIC_HEAD,
}
# Narx yoki aksiya bo'lsa — sotuv rahbari + direktor
APPROVAL_PRICE = [SALES_HEAD, FOUNDER]
APPROVAL_OFFICIAL = FOUNDER

APPROVAL_DECISIONS = [
    ("approved", "Tasdiqlandi", "emerald"),
    ("changes", "O'zgartirish kerak", "amber"),
    ("rejected", "Rad etildi", "red"),
    ("info", "Qo'shimcha ma'lumot kerak", "sky"),
]
APPROVAL_LABELS = {k: lbl for k, lbl, _ in APPROVAL_DECISIONS}
APPROVAL_TONE = {k: t for k, _, t in APPROVAL_DECISIONS}

# ---- G'oyalar bazasi ----
IDEA_STATUSES = [
    ("new", "Yangi", "sky"),
    ("review", "Ko'rib chiqilmoqda", "amber"),
    ("accepted", "Qabul qilindi", "emerald"),
    ("converted", "Kontentga aylantirildi", "teal"),
    ("later", "Keyinga qoldirildi", "slate"),
    ("rejected", "Rad etildi", "red"),
    ("used", "Ishlatildi", "violet"),
]
IDEA_STATUS_LABELS = {k: lbl for k, lbl, _ in IDEA_STATUSES}
IDEA_STATUS_TONE = {k: t for k, _, t in IDEA_STATUSES}

# ---- Ichki so'rovlar ----
REQUEST_STATUSES = [
    ("new", "Yangi", "sky"),
    ("clarify", "Aniqlashtirish kerak", "amber"),
    ("accepted", "Qabul qilindi", "emerald"),
    ("in_work", "Ishda", "teal"),
    ("done", "Bajarildi", "slate"),
    ("rejected", "Rad etildi", "red"),
]
REQUEST_STATUS_LABELS = {k: lbl for k, lbl, _ in REQUEST_STATUSES}
REQUEST_STATUS_TONE = {k: t for k, _, t in REQUEST_STATUSES}

# ---- Media roziligi ----
CONSENT_STATUSES = [
    ("ok", "Rozilik mavjud", "emerald"),
    ("internal", "Faqat ichki foydalanish", "amber"),
    ("social", "Ijtimoiy tarmoqqa mumkin", "teal"),
    ("no_face", "Yuzini ko'rsatish mumkin emas", "orange"),
    ("pending", "Ota-ona tasdig'i kutilmoqda", "sky"),
    ("forbidden", "Foydalanish taqiqlangan", "red"),
]
CONSENT_LABELS = {k: lbl for k, lbl, _ in CONSENT_STATUSES}
CONSENT_TONE = {k: t for k, _, t in CONSENT_STATUSES}
# Shu holatlarda ijtimoiy tarmoqqa joylashga RUXSAT BERILMAYDI
CONSENT_BLOCKS_PUBLISH = ["internal", "pending", "forbidden"]

# ---- Kontent reja bajarilishi ----
PLAN_TARGET_PERCENT = 80.0     # bundan past bo'lsa ogohlantiriladi

# ---- Sifatli engagement ballari (admin sozlashi mumkin) ----
ENGAGEMENT_WEIGHTS = [
    ("like", "Like", 1),
    ("comment", "Izoh", 2),
    ("save", "Saqlash", 3),
    ("share", "Ulashish", 4),
    ("dm", "DM", 5),
]
ENGAGEMENT_WEIGHT_MAP = {k: w for k, _l, w in ENGAGEMENT_WEIGHTS}

# ---- SMM KPI modeli ----
SMM_KPI_WEIGHTS = [
    ("plan", "Kontent reja va intizom", 20),
    ("leads", "Sifatli leadlar", 25),
    ("engagement", "Engagement sifati", 15),
    ("sales", "Sotuvga ta'siri", 15),
    ("inbox", "DM va community", 10),
    ("brand", "Brand standartiga rioya", 10),
    ("experiment", "Yangi formatlar", 5),
]
SMM_KPI_LABELS = {k: lbl for k, lbl, _ in SMM_KPI_WEIGHTS}

# ---- Ruxsatlar ----
SMM_ACCESS = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD]
CONTENT_REQUESTER = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
                                   BRANCH_MANAGER, ACADEMIC_HEAD,
                                   ADMINISTRATOR]
IDEA_SUBMIT = STAFF_ROLES        # g'oyani har qanday xodim yuboradi


# =====================================================================
#  SMM: SOCIAL INBOX VA ATRIBUTSIYA
#
#  Ikkita savolga javob beradi:
#    1. Kimga javob berilmagan va qancha vaqt kutdi?
#    2. Qaysi kontent qancha sotuv olib keldi?
#
#  Ikkinchisi eng muhimi: "bu video 200 000 ko'rildi" degan gap
#  o'zicha hech narsani anglatmaydi. "200 000 ko'rishdan 430 murojaat,
#  118 sifatli lead, 37 sotuv va 15,5 mln so'm tushum" — mana bu gap.
# =====================================================================
INBOX_CHANNELS = [
    ("instagram", "Instagram", "rose"),
    ("telegram", "Telegram", "sky"),
    ("tiktok", "TikTok", "slate"),
    ("youtube", "YouTube", "red"),
    ("facebook", "Facebook", "sky"),
    ("website", "Sayt chati", "teal"),
    ("form", "Formadan", "emerald"),
]
CHANNEL_LABELS = {k: lbl for k, lbl, _ in INBOX_CHANNELS}
CHANNEL_TONE = {k: t for k, _, t in INBOX_CHANNELS}

MESSAGE_KINDS = [
    ("dm", "Shaxsiy xabar"),
    ("comment", "Izoh"),
    ("mention", "Mention"),
    ("story_reply", "Story javobi"),
    ("form", "Forma"),
    ("chat", "Sayt chati"),
]
MESSAGE_KIND_LABELS = dict(MESSAGE_KINDS)

INBOX_STATUSES = [
    ("new", "Yangi", "sky"),
    ("answered", "Javob berildi", "teal"),
    ("lead", "Leadga aylantirildi", "emerald"),
    ("sent_sales", "Sotuvchiga yuborildi", "violet"),
    ("complaint", "Shikoyat", "red"),
    ("spam", "Spam", "slate"),
    ("waiting", "Javob kutilmoqda", "amber"),
    ("done", "Yakunlandi", "slate"),
]
INBOX_STATUS_LABELS = {k: lbl for k, lbl, _ in INBOX_STATUSES}
INBOX_STATUS_TONE = {k: t for k, _, t in INBOX_STATUSES}
INBOX_OPEN = ["new", "waiting"]

# ---- Javob vaqti (SLA) ----
# Ish vaqtidan tashqari kelgan murojaatlar alohida hisoblanadi —
# aks holda tunda kelgan xabar uchun SMM aybdor bo'lib qolardi.
SLA_BANDS = [
    (15, "good", "Yaxshi", "emerald"),
    (30, "ok", "Qoniqarli", "teal"),
    (60, "late", "Kechikish", "amber"),
    (None, "critical", "Kritik", "red"),
]
SLA_ALERT_MINUTES = 30       # bundan ko'p javobsiz qolsa dashboardda chiqadi
INBOX_WORK_START = "09:00"
INBOX_WORK_END = "20:00"


def sla_band(minutes: float | None) -> tuple:
    """Javob vaqtidan xulosa: (kalit, matn, rang)."""
    if minutes is None:
        return ("pending", "Javob kutilmoqda", "slate")
    for limit, key, label, tone in SLA_BANDS:
        if limit is None or minutes <= limit:
            return (key, label, tone)
    return ("critical", "Kritik", "red")


# ---- Tezkor javob shablonlari ----
QUICK_REPLIES = [
    ("price", "Kurs narxi",
     "Assalomu alaykum! Oylik to'lov {narx} so'm. Ichida kitob, "
     "qo'shimcha darslar va yakshanba tadbirlari bor. Qaysi filial "
     "sizga qulay?"),
    ("address", "Filial manzili",
     "Filiallarimiz: {manzil}. Sizga qaysi biri yaqin?"),
    ("time", "Dars vaqti",
     "Guruhlar ertalab va kechqurun bor. Sizga qaysi vaqt qulay?"),
    ("ielts", "IELTS guruhi",
     "IELTS guruhimiz bor. Hozirgi darajangizni bilish uchun bepul "
     "test topshirasiz, keyin mos guruhga qo'yamiz."),
    ("cefr", "CEFR guruhi",
     "CEFR guruhimiz bor. Bepul daraja aniqlash testidan boshlaymiz."),
    ("trial", "Sinov darsi",
     "Bepul sinov darsiga yozilishingiz mumkin. Ism-familiyangiz va "
     "telefon raqamingizni yozib qoldiring."),
    ("phone", "Telefon raqami",
     "Bog'lanish uchun: {telefon}"),
    ("signup", "Ro'yxatdan o'tish",
     "Ro'yxatdan o'tish uchun ism-familiya va telefon raqamingizni "
     "yozing — administratorimiz bog'lanadi."),
    ("grant", "Grant",
     "Grant va chegirmalar haqida batafsil ma'lumot beramiz. "
     "Telefon raqamingizni qoldiring."),
    ("mock", "Mock exam",
     "Mock IELTS testimiz bor — haqiqiy imtihondagidek. Qatnashish "
     "uchun oldindan yozilish kerak."),
]
QUICK_REPLY_LABELS = {k: lbl for k, lbl, _ in QUICK_REPLIES}

# ---- Atributsiya voronkasi ----
ATTRIBUTION_FUNNEL = [
    ("reach", "Qamrov"),
    ("engagement", "Faol harakat"),
    ("profile", "Profil tashrifi"),
    ("click", "Havola bosilishi"),
    ("dm", "Murojaat"),
    ("lead", "Lead"),
    ("qualified", "Sifatli lead"),
    ("trial", "Sinov darsi"),
    ("sale", "Sotuv"),
    ("retained", "30 kun qoldi"),
]
FUNNEL_ORDER = [k for k, _ in ATTRIBUTION_FUNNEL]
ATTR_FUNNEL_LABELS = dict(ATTRIBUTION_FUNNEL)

# Sifatli lead: telefon raqami bor va kursga aniq qiziqqan
QUALIFIED_STAGES = ["contacted", "trial_scheduled", "trial_done",
                    "negotiation", "won"]
RETENTION_DAYS = [30, 90]

INBOX_ACCESS = FULL_ACCESS + [SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
                              ADMINISTRATOR]


# =====================================================================
#  BREND KITOB
#
#  Manba: "Jony Academy brandbook 2023" (rasmiy PDF).
#  PDF'da bo'lmagan, lekin amalda kerak bo'lgan qoidalar quyida
#  "TO'LDIRILDI" izohi bilan berilgan — asoschi ularni tasdiqlashi
#  yoki o'zgartirishi kerak.
# =====================================================================

BRAND_SOURCE = "Jony Academy brandbook 2023"

# ---- Ranglar (PDF, 2-sahifa) ----
BRAND_COLORS = [
    # (kalit, nom, hex, turi, izoh)
    ("primary", "Asosiy ko'k", "#1A6FE4", "primary",
     "R 26 · G 111 · B 228. Logotip, tugmalar, asosiy urg'u."),
    ("secondary", "Ikkilamchi ko'k", "#4375B9", "primary",
     "C 82 · M 56 · Y 0 · K 0. Bosma va ikkinchi darajali elementlar."),
    # TO'LDIRILDI: brandbookda faqat 2 ta ko'k bor. Interfeys va
    # postlar uchun holat ranglari kerak — quyidagilar asosiy ko'k
    # bilan uyg'un tanlandi.
    ("ink", "Matn qorasi", "#111827", "neutral",
     "TO'LDIRILDI. Asosiy matn. Sof qora (#000000) ekranda qattiq."),
    ("paper", "Oq fon", "#FFFFFF", "neutral", "Asosiy fon."),
    ("mist", "Och kulrang", "#F1F3F6", "neutral",
     "TO'LDIRILDI. Blok fonlari, ajratgichlar."),
    ("success", "Yashil", "#10B981", "state",
     "TO'LDIRILDI. Faqat interfeysda: muvaffaqiyat, tasdiq."),
    ("warning", "Sariq", "#F59E0B", "state",
     "TO'LDIRILDI. Faqat interfeysda: ogohlantirish."),
    ("danger", "Qizil", "#EF4444", "state",
     "TO'LDIRILDI. Faqat interfeysda: xato, kechikish."),
]
BRAND_PRIMARY = "#1A6FE4"
BRAND_SECONDARY = "#4375B9"
# Postda faqat shu ranglar ishlatiladi (holat ranglari — interfeys uchun)
BRAND_POST_COLORS = ["#1A6FE4", "#4375B9", "#FFFFFF", "#111827", "#F1F3F6"]

# ---- Shriftlar (PDF, 3-sahifa) ----
BRAND_FONTS = [
    ("HelveticaNeueCyr", "Asosiy shrift",
     "Brandbookda belgilangan. Bosma va dizayn ishlari uchun."),
    # TO'LDIRILDI: HelveticaNeueCyr veb va telefonda yo'q.
    ("Inter", "Veb uchun zaxira",
     "TO'LDIRILDI. Brauzerda HelveticaNeueCyr topilmaydi — Inter eng "
     "yaqin ko'rinishni beradi."),
    ("Arial", "Hujjat uchun zaxira",
     "TO'LDIRILDI. Word va Google Docs uchun."),
]

# ---- Logotip (PDF, 4–7-sahifalar) ----
LOGO_RULES = [
    ("Xavfsizlik maydoni", "PDF",
     "Logotip atrofida bo'sh joy: yon tomonlarda X, yuqori va pastda "
     "0.5X. X — belgi (kvadrat) balandligi. Bu maydonga hech narsa "
     "kirmaydi."),
    ("Ruxsat etilgan fonlar", "PDF",
     "Ko'k (#1A6FE4), oq, och kulrang, qora. Har birida logotipning "
     "mos varianti ishlatiladi."),
    ("Oq fonda", "PDF", "Ko'k belgi + qora yozuv."),
    ("Ko'k fonda", "PDF", "Oq belgi + oq yozuv."),
    ("Qora fonda", "PDF", "Ko'k yoki oq belgi + oq yozuv."),
    # TO'LDIRILDI
    ("Eng kichik o'lcham", "TO'LDIRILDI",
     "Ekranda 24 px balandlik, bosmada 10 mm. Bundan kichik bo'lsa "
     "belgi o'qilmay qoladi."),
    ("Rasm ustida", "TO'LDIRILDI",
     "Faqat sokin, bir tekis joyda. Rasm band bo'lsa logotip ostiga "
     "60% shaffof qatlam qo'yiladi."),
]
LOGO_DONTS = [
    "Cho'zish yoki siqish — nisbat o'zgarmaydi.",
    "Rangini o'zgartirish — brendbookdagi variantlardan boshqasi yo'q.",
    "Burish yoki qiyalatish.",
    "Soya, kontur, gradient yoki effekt qo'shish.",
    "Yozuvni belgidan ajratib, boshqa joyga qo'yish.",
    "Yozuvni boshqa shriftga almashtirish.",
    "Band rasm ustiga to'g'ridan-to'g'ri qo'yish.",
    "Xavfsizlik maydoniga matn yoki boshqa logotip kiritish.",
]

# ---- Rasmiy rekvizitlar (PDF, 14-sahifa: vizitka) ----
BRAND_CONTACTS = [
    ("Sayt", "www.jonyacademy.uz", ""),
    ("Email", "jonyacademy@gmail.com",
     "TO'LDIRILDI. Brandbookda 'jonyacademy.gmail.com' deb yozilgan — "
     "@ belgisi tushib qolgan, ya'ni bu ishlamaydigan manzil. "
     "Tasdiqlang."),
]

# ---- Brend so'zi (TO'LDIRILDI — brandbookda yo'q) ----
BRAND_WORD = "Muhit"
BRAND_WORD_NOTE = (
    "TO'LDIRILDI. Brandbookda pozitsiyalash so'zi yo'q. Jony nomi "
    "eshitilganda odam ongida bitta so'z tiklanishi kerak — 'muhit'. "
    "Ya'ni faqat dastur yoki narx emas, bolani o'rab turgan butun "
    "muhit: ustozlar, tengdoshlar, kayfiyat, munosabat."
)

# ---- Ovoz va uslub (TO'LDIRILDI — brandbookda yo'q) ----
TONE_RULES = [
    ("Odamga o'xshab yoz", "do",
     "Birovga gapirayotgandek. 'Hurmatli ota-onalar, sizni xabardor "
     "qilib o'tamizki…' — bunday yozilmaydi."),
    ("Birinchi jumla ushlab qolsin", "do",
     "Telegramda odam bir soniyada scroll qiladi. Birinchi qator "
     "savol, kutilmagan gap yoki his bo'lsin."),
    ("Xususiyat emas — foyda", "do",
     "'Tajribali ustozlar' emas — 'farzandingiz uyda \"tushunmadim\" "
     "demay, o'zi masala yechadi'."),
    ("Aniq raqam", "do",
     "'Ko'p natija' emas — '100+ IELTS sertifikati'. 'Muntazam' emas "
     "— 'haftasiga 3 marta'."),
    ("Ijobiy tasvir", "do",
     "'Qo'rqmaydi' emas — 'ishonch bilan kiradi'. Miya inkorni ham "
     "avval tasvir qilib ko'radi."),
    ("Qisqa jumla", "do",
     "Har vergul oldida so'ra: nuqta bo'lsa bo'ladimi? Ko'pincha ha."),
    ("Yo'q narsani yozma", "dont",
     "Berilmagan natija, kafolat yoki raqamni o'ylab topish "
     "taqiqlanadi. Bitta bo'rttirilgan post uzoq muddatda ishonchni "
     "yo'q qiladi."),
    ("Mavhum maqtov", "dont",
     "'Sifatli', 'zamonaviy', 'eng yaxshi' — hech qanday tasvir "
     "chizmaydi, o'quvchi miyasi o'tkazib yuboradi."),
    ("Narxda 'dan'", "dont",
     "Narx qat'iy bo'lsa '480 000 so'mdan' emas, '480 000 so'm'. "
     "'dan' manipulyatsiya bo'lib tuyuladi."),
    ("Ortiqcha undov", "dont",
     "Samimiylik — undov belgisi emas. Sotuvchi ohangda gapirma."),
]

# ---- Ijtimoiy tarmoq o'lchamlari (TO'LDIRILDI) ----
SOCIAL_SPECS = [
    ("Instagram post", "1080×1350", "4:5 eng ko'p joy egallaydi."),
    ("Instagram Reels", "1080×1920", "9:16. Pastki 250 px va yuqori "
     "150 px — interfeys bosib qoladi, muhim narsa qo'yilmaydi."),
    ("Instagram Stories", "1080×1920", "9:16."),
    ("Telegram post rasmi", "1280×720", "16:9."),
    ("YouTube preview", "1280×720", "16:9."),
    ("Profil rasmi", "512×512", "Doira ichida kesiladi — belgi "
     "markazda, yozuvsiz."),
]

# ---- Kontentni brend bo'yicha tekshirish ----
BRAND_CHECKS = [
    ("logo", "Logotip to'g'ri variantda va xavfsizlik maydoni saqlangan"),
    ("color", "Faqat brend ranglari ishlatilgan"),
    ("font", "Shrift brendbookka mos"),
    ("tone", "Matn brend ovoziga mos, mavhum maqtov yo'q"),
    ("claim", "Har bir raqam va natija haqiqiy, tekshirilgan"),
    ("consent", "Rasmdagi odamlarning roziligi bor"),
    ("contact", "Aloqa ma'lumotlari to'g'ri"),
]
BRAND_CHECK_LABELS = {k: lbl for k, lbl in BRAND_CHECKS}
# Nashrdan oldin majburiy
BRAND_CHECK_REQUIRED = ["claim", "consent"]

BRAND_GAPS = [
    "Ovoz va uslub (tone of voice) — brandbookda umuman yo'q.",
    "Logotipni ishlatmaslik qoidalari ('shunday qilma') yo'q.",
    "Logotipning eng kichik o'lchami ko'rsatilmagan.",
    "Ijtimoiy tarmoq o'lchamlari yo'q (2023-da hali dolzarb emas edi).",
    "Veb uchun zaxira shrift yo'q — HelveticaNeueCyr brauzerda yo'q.",
    "Holat ranglari (muvaffaqiyat/ogohlantirish/xato) yo'q.",
    "Rasm uslubi (fotografiya qoidalari) yo'q.",
    "Vizitkadagi email manzilida @ belgisi tushib qolgan.",
    "Jony School uchun alohida bo'lim yo'q — brandbook 2023-yilda "
    "faqat Academy uchun tuzilgan.",
]

BRAND_EDIT = FULL_ACCESS + [SMM_MANAGER]


# =====================================================================
#  BILIMLAR BAZASI
# =====================================================================

KB_CATEGORIES = [
    ("brand", "Brend qoidalari", "sky"),
    ("process", "Jarayon va reglament", "violet"),
    ("template", "Shablon va namuna", "teal"),
    ("faq", "Tez-tez so'raladigan savollar", "amber"),
    ("crisis", "Inqiroz va nozik holatlar", "red"),
    ("tool", "Dastur va texnika", "slate"),
]
KB_CATEGORY_LABELS = {k: lbl for k, lbl, _ in KB_CATEGORIES}
KB_CATEGORY_TONE = {k: t for k, _, t in KB_CATEGORIES}
KB_REVIEW_MONTHS = 6          # shundan keyin "eskirgan" deb belgilanadi


# =====================================================================
#  MEDIA KUTUBXONA
# =====================================================================

MEDIA_KINDS = [
    ("photo", "Foto", "sky"),
    ("video", "Video", "violet"),
    ("raw", "Xom material", "slate"),
    ("design", "Dizayn (Canva/PSD)", "teal"),
    ("logo", "Logotip va brend fayl", "amber"),
    ("doc", "Hujjat", "slate"),
]
MEDIA_KIND_LABELS = {k: lbl for k, lbl, _ in MEDIA_KINDS}
MEDIA_KIND_TONE = {k: t for k, _, t in MEDIA_KINDS}
CONSENT_EXPIRY_WARN_DAYS = 30     # rozilik tugashiga shuncha kun qolganda


# =====================================================================
#  SMM ANALITIKA VA HISOBOT
# =====================================================================

ANALYTICS_DIMENSIONS = [
    ("platform", "Platforma"),
    ("format", "Format"),
    ("pillar", "Yo'nalish"),
    ("branch", "Filial"),
    ("course", "Kurs"),
    ("author", "Muallif"),
    ("goal", "Maqsad"),
    ("weekday", "Hafta kuni"),
]
# Analitika kesimi uchun soddalashtirilgan formatlar ro'yxati.
# DIQQAT: nomi ataylab boshqa — CONTENT_FORMATS kontent-quvurniki,
# ikkinchi marta e'lon qilinsa uni jimgina almashtirib yuborardi.
ANALYTICS_FORMATS = [
    ("reels", "Reels / qisqa video"),
    ("carousel", "Karusel"),
    ("photo", "Bitta rasm"),
    ("story", "Story"),
    ("text", "Matn"),
    ("live", "Jonli efir"),
    ("long", "Uzun video"),
]
# Quvur kalitlari ham yorliq topsin, lekin umumiy kalitlarda
# analitika yorlig'i ustun — avvalgi xatti-harakat saqlanadi
CONTENT_FORMAT_LABELS = {**FORMAT_LABELS,
                         **{k: lbl for k, lbl in ANALYTICS_FORMATS}}
UZ_WEEKDAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba",
               "Juma", "Shanba", "Yakshanba"]

REPORT_PERIODS = [
    ("week", "Haftalik"),
    ("month", "Oylik"),
    ("quarter", "Choraklik"),
]
REPORT_SECTIONS = [
    ("summary", "Qisqacha xulosa"),
    ("plan", "Reja bajarilishi"),
    ("funnel", "Qamrovdan sotuvgacha"),
    ("top", "Eng yaxshi kontentlar"),
    ("weak", "Ishlamagan kontentlar"),
    ("inbox", "Murojaatlar va SLA"),
    ("dimensions", "Kesimlar tahlili"),
    ("kpi", "SMM KPI"),
    ("next", "Keyingi davr uchun tavsiya"),
]
REPORT_SECTION_LABELS = {k: lbl for k, lbl in REPORT_SECTIONS}

# KPI bahosi
KPI_BANDS = [
    (90, "Ajoyib", "emerald"),
    (75, "Yaxshi", "teal"),
    (60, "Qoniqarli", "amber"),
    (0, "Past", "red"),
]


def kpi_band(score):
    """KPI ballidan baho va rang."""
    for floor, label, tone in KPI_BANDS:
        if score >= floor:
            return label, tone
    return "Past", "red"


def format_of(platform, kind=None):
    """Platformadan formatni taxmin qiladi."""
    p = (platform or "").lower()
    if "reels" in p or "tiktok" in p or "shorts" in p:
        return "reels"
    if "story" in p or "stories" in p:
        return "story"
    if "youtube" in p:
        return "long"
    if "telegram" in p:
        return "text"
    return kind or "photo"


# =====================================================================
#  AVTOMAT AKKAUNT — login va parol
#
#  Ustoz uchun akkaunt bir tugma bilan ochiladi. Login ismdan
#  yasaladi, parol tasodifiy. Parol bazada faqat shifrlangan holda
#  saqlanadi — bir marta ko'rsatiladi, keyin qayta o'qib bo'lmaydi.
# =====================================================================

# O'zbek harflarini lotin login uchun soddalashtirish
TRANSLIT = {
    "o'": "o", "g'": "g", "O'": "o", "G'": "g",
    "ʻ": "", "ʼ": "", "'": "", "`": "", "’": "", "‘": "",
    "ў": "o", "ғ": "g", "қ": "q", "ҳ": "h",
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
    "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
    "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def translit(text: str) -> str:
    """Ismni loginga yaroqli lotin harflariga o'giradi."""
    s = (text or "").strip().lower()
    for a, b in TRANSLIT.items():
        s = s.replace(a.lower(), b)
    return "".join(ch for ch in s if ch.isalnum() or ch in " -")


def login_from_name(full_name: str) -> str:
    """'Bekzod Nabijonov' -> 'bekzod.nabijonov'. Takrorlanish
    tekshiruvi chaqiruvchi tomonda."""
    parts = [p for p in translit(full_name).replace("-", " ").split() if p]
    if not parts:
        return "xodim"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}.{parts[-1]}"


# Chalkashtiradigan belgilar yo'q: i, l, I, 1, o, O, 0 ishlatilmaydi
PWD_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
PWD_LENGTH = 8


def make_password() -> str:
    """Telefonda aytib berish oson bo'lsin uchun 4+4 ko'rinishida."""
    import secrets
    raw = "".join(secrets.choice(PWD_ALPHABET) for _ in range(PWD_LENGTH))
    return raw[:4] + "-" + raw[4:]


# Kim akkaunt ocha oladi
ACCOUNT_MANAGE = FULL_ACCESS + [HR_MANAGER]


# =====================================================================
#  USTOZNING O'Z NATIJALARI
#
#  Ustoz o'zining ko'rsatkichlarini ko'radi: nechta o'quvchi qoldi,
#  nechtasi ketdi, o'rtacha qancha oy o'qidi va bu markaz o'rtachasidan
#  baland yoki pastmi.
#
#  Boshqa ustozlarning ismi KO'RSATILMAYDI — faqat o'rtacha va o'rin.
#  Aks holda bu tahlil emas, g'iybat manbaiga aylanadi.
# =====================================================================

SELF_STATS = [TEACHER, SUPPORT_TEACHER]

# Ketganlar ro'yxati shu oynalar bo'yicha bo'linadi
LEAVER_WINDOWS = [
    ("month", "Shu oyda", 0),        # 0 = joriy oy boshidan
    ("m2", "Oxirgi 2 oy", 60),
    ("m6", "Oxirgi 6 oy", 180),
    ("y1", "Oxirgi 1 yil", 365),
]

# Solishtirish uchun eng kam ustoz soni — bittada o'rtacha ma'nosiz
MIN_PEERS_FOR_RANK = 3
# Ko'rsatkich ishonchli bo'lishi uchun kamida shuncha o'quvchi kerak
MIN_STUDENTS_FOR_STATS = 5


def compare_verdict(mine, avg, lower_is_better=False):
    """Ustozning ko'rsatkichi o'rtachaga nisbatan qanday.
    Qaytaradi: (matn, rang, farq foizi)."""
    if avg is None or mine is None or avg == 0:
        return "Solishtirish uchun ma'lumot yetarli emas", "slate", None
    diff = round((mine - avg) / avg * 100, 1)
    better = (mine < avg) if lower_is_better else (mine > avg)
    if abs(diff) < 5:
        return "O'rtacha darajada", "slate", diff
    if better:
        return "O'rtachadan yaxshi", "emerald", diff
    return "O'rtachadan past", "amber", diff


# =====================================================================
#  HR: BO'LIMLAR VA LAVOZIMLAR
#
#  Bular jadval sifatida saqlanadi (asoschi tahrirlashi kerak), lekin
#  boshlang'ich ro'yxat shu yerdan seed qilinadi.
# =====================================================================

DEPARTMENTS = [
    ("academic", "O'quv bo'limi", "Ustozlar, support, examiner"),
    ("sales", "Sotuv", "Lidlar, sinov darsi, shartnoma"),
    ("marketing", "Marketing", "SMM, reklama, kontent"),
    ("hr", "HR", "Kadrlar va rivojlanish"),
    ("finance", "Moliya", "Kassa, hisobot, oylik"),
    ("operations", "Operatsiya", "Filial ishi, jadval, xona"),
    ("admin", "Ma'muriyat", "Administratorlar, qabul"),
    ("it", "IT", "Tizim va texnika"),
]
DEPARTMENT_LABELS = {k: lbl for k, lbl, _ in DEPARTMENTS}

# (kalit, nom, bo'lim, tizimdagi rol, sinov muddati oyi, sinov darsi
#  kerakmi)
POSITIONS = [
    ("teacher", "O'qituvchi", "academic", TEACHER, 2, True),
    ("senior_teacher", "Katta o'qituvchi", "academic", TEACHER, 1, True),
    ("support_teacher", "Support teacher", "academic", SUPPORT_TEACHER,
     2, True),
    ("examiner", "Examiner", "academic", EXAMINER, 2, True),
    ("academic_head", "O'quv bo'limi rahbari", "academic", ACADEMIC_HEAD,
     3, False),
    ("administrator", "Administrator", "admin", ADMINISTRATOR, 2, False),
    ("sales_manager", "Sotuv menejeri", "sales", SALES_MANAGER, 2, False),
    ("sales_head", "Sotuv rahbari", "sales", SALES_HEAD, 3, False),
    ("smm_manager", "SMM menejer", "marketing", SMM_MANAGER, 2, False),
    ("hr_manager", "HR menejer", "hr", HR_MANAGER, 3, False),
    ("recruiter", "Rekruter", "hr", HR_MANAGER, 2, False),
    ("accountant", "Buxgalter", "finance", ACCOUNTANT, 3, False),
    ("branch_manager", "Filial rahbari", "operations", BRANCH_MANAGER,
     3, False),
    ("videographer", "Videograf", "marketing", SMM_MANAGER, 2, False),
    ("designer", "Dizayner", "marketing", SMM_MANAGER, 2, False),
]
POSITION_LABELS = {k: lbl for k, lbl, _d, _r, _p, _t in POSITIONS}
# Qaysi lavozimda sinov darsi majburiy
TRIAL_REQUIRED = [k for k, _l, _d, _r, _p, t in POSITIONS if t]
DEFAULT_PROBATION_MONTHS = 2


# =====================================================================
#  HR: SHTAT REJASI (WORKFORCE PLANNING)
#
#  "Qaysi filialda nechta odam kerak?" degan savolga raqam bilan javob
#  beradi. Bo'shliq = tasdiqlangan shtat − hozirgi faol xodim.
# =====================================================================

PLAN_STATUSES = [
    ("draft", "Qoralama", "slate"),
    ("review", "Ko'rib chiqilmoqda", "amber"),
    ("approved", "Tasdiqlandi", "emerald"),
    ("active", "Amalda", "teal"),
    ("closed", "Yopildi", "slate"),
]
PLAN_STATUS_LABELS = {k: lbl for k, lbl, _ in PLAN_STATUSES}
PLAN_STATUS_TONE = {k: t for k, _, t in PLAN_STATUSES}

# Ustoz yuklamasi darajalari (admin sozlashi mumkin)
UTILIZATION_BANDS = [
    (40, "low", "Bo'sh", "sky"),
    (70, "normal", "Me'yorida", "emerald"),
    (90, "high", "Band", "amber"),
    (None, "over", "Ortiqcha yuklangan", "red"),
]


def utilization_band(percent):
    """Yuklama foizidan daraja va rang."""
    for ceiling, key, label, tone in UTILIZATION_BANDS:
        if ceiling is None or percent <= ceiling:
            return key, label, tone
    return "over", "Ortiqcha yuklangan", "red"


# =====================================================================
#  HR: YANGI XODIM SO'ROVI
#
#  Filial rahbari og'zaki emas, tizim orqali so'raydi. Tasdiqlanmagan
#  so'rov bo'yicha vakansiya ochilmaydi — bu byudjetni himoya qiladi.
# =====================================================================

REQUEST_REASONS = [
    ("new_group", "Yangi guruh ochilyapti", False),
    ("new_branch", "Yangi filial", False),
    ("resigned", "Xodim ishdan bo'shadi", True),
    ("terminated", "Xodim ishdan chiqarildi", True),
    ("workload", "Yuklama oshdi", False),
    ("new_position", "Yangi lavozim", False),
    ("temporary", "Vaqtinchalik o'rinbosar", True),
    ("performance", "Natijasi past xodim o'rniga", True),
    ("seasonal", "Mavsumiy ehtiyoj", False),
    ("other", "Boshqa", False),
]
REQUEST_REASON_LABELS = {k: lbl for k, lbl, _ in REQUEST_REASONS}
# Shu sabablarda kimning o'rniga ekani ko'rsatilishi kerak
REPLACEMENT_REASONS = [k for k, _l, r in REQUEST_REASONS if r]

STAFF_REQUEST_FLOW = [
    ("draft", "Qoralama", "slate"),
    ("submitted", "Yuborildi", "sky"),
    ("hr_review", "HR ko'rmoqda", "violet"),
    ("budget_review", "Byudjet ko'rmoqda", "amber"),
    ("director_review", "Rahbar ko'rmoqda", "orange"),
    ("approved", "Tasdiqlandi", "emerald"),
    ("rejected", "Rad etildi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
    ("converted", "Vakansiya ochildi", "teal"),
]
REQUEST_STATE_LABELS = {k: lbl for k, lbl, _ in STAFF_REQUEST_FLOW}
REQUEST_STATE_TONE = {k: t for k, _, t in STAFF_REQUEST_FLOW}

# Tasdiqlash zanjiri: har bir bosqichda kim qaror qabul qiladi
REQUEST_APPROVERS = {
    "submitted": [HR_MANAGER] + FULL_ACCESS,
    "hr_review": [ACCOUNTANT, FOUNDER],
    "budget_review": [FOUNDER],
}
REQUEST_NEXT = {
    "submitted": "hr_review",
    "hr_review": "budget_review",
    "budget_review": "approved",
}
# Bu bosqichdan keyin so'rovni tahrirlab bo'lmaydi
REQUEST_LOCKED_AFTER = ["approved", "rejected", "cancelled", "converted"]

REQUEST_PRIORITIES = [
    ("low", "Past", "slate", 60),
    ("normal", "Oddiy", "sky", 30),
    ("high", "Yuqori", "amber", 14),
    ("critical", "Kritik", "red", 7),
]
PRIORITY_LABELS = {k: lbl for k, lbl, _t, _d in REQUEST_PRIORITIES}
PRIORITY_TONE = {k: t for k, _l, t, _d in REQUEST_PRIORITIES}
# Vakansiya shuncha kundan ortiq ochiq qolsa ogohlantiriladi
PRIORITY_SLA_DAYS = {k: d for k, _l, _t, d in REQUEST_PRIORITIES}

EMPLOYMENT_TYPES = [
    ("full", "To'liq stavka"),
    ("part", "Yarim stavka"),
    ("hourly", "Soatbay"),
    ("contract", "Shartnoma asosida"),
    ("intern", "Amaliyotchi"),
]
EMPLOYMENT_TYPE_LABELS = dict(EMPLOYMENT_TYPES)


# =====================================================================
#  HR: VAKANSIYA
# =====================================================================

VACANCY_STATES = [
    ("draft", "Qoralama", "slate"),
    ("pending", "Tasdiq kutilmoqda", "amber"),
    ("open", "Ochiq", "emerald"),
    ("sourcing", "Nomzod qidirilmoqda", "sky"),
    ("screening", "Rezyumelar ko'rilmoqda", "sky"),
    ("interviewing", "Suhbatlar", "violet"),
    ("assessment", "Sinov bosqichi", "violet"),
    ("offer", "Taklif bosqichi", "orange"),
    ("partial", "Qisman to'ldirildi", "teal"),
    ("filled", "To'ldirildi", "teal"),
    ("hold", "To'xtatib turildi", "slate"),
    ("cancelled", "Bekor qilindi", "slate"),
    ("closed", "Yopildi", "slate"),
]
VACANCY_STATE_LABELS = {k: lbl for k, lbl, _ in VACANCY_STATES}
VACANCY_STATE_TONE = {k: t for k, _, t in VACANCY_STATES}
# Shu holatlarda vakansiya "ochiq" hisoblanadi
VACANCY_OPEN_STATES = ["open", "sourcing", "screening", "interviewing",
                       "assessment", "offer", "partial"]

VACANCY_CLOSE_REASONS = [
    ("filled", "Xodim topildi"),
    ("no_need", "Ehtiyoj qolmadi"),
    ("budget", "Byudjet yo'q"),
    ("internal", "Ichki xodim bilan yopildi"),
    ("postponed", "Keyinga qoldirildi"),
    ("other", "Boshqa"),
]
CLOSE_REASON_LABELS = dict(VACANCY_CLOSE_REASONS)


# ---- HR ruxsatlari ----
HR_FULL = FULL_ACCESS + [HR_MANAGER]
WORKFORCE_VIEW = HR_FULL + [ACCOUNTANT, ACADEMIC_HEAD]
REQUEST_CREATE = FULL_ACCESS + [HR_MANAGER, ACADEMIC_HEAD, SALES_HEAD]
VACANCY_MANAGE = HR_FULL


# =====================================================================
#  VAQT MINTAQASI
#
#  Server UTC'da ishlaydi, markaz esa Toshkent vaqtida. Ish vaqti,
#  "bugun" va SLA hisobida shu farq hisobga olinmasa, soat 21:00 da
#  kelgan xabar "ish vaqtida keldi" deb sanaladi va xodim aybdor
#  bo'lib qoladi.
#
#  Boshqa mamlakatda filial ochilsa shu qiymat o'zgartiriladi.
# =====================================================================
TIMEZONE_OFFSET_HOURS = 5          # O'zbekiston: UTC+5


def to_local(when):
    """UTC vaqtni markaz vaqtiga o'giradi."""
    from datetime import timedelta as _td
    if when is None:
        return None
    return when + _td(hours=TIMEZONE_OFFSET_HOURS)


def local_now():
    from datetime import datetime as _dt
    return to_local(_dt.utcnow())


def local_today():
    return local_now().date()


# =====================================================================
#  XODIM KARTASI: KO'RISH, TAHRIRLASH, ROL BERISH
#
#  Bu uch narsa alohida huquq. Ilgari uchalasi ham USER_ADMIN
#  (faqat asoschi) ostida edi — natijada HR menejer xodimlar
#  ro'yxatini umuman ocholmasdi.
#
#  Endi:
#    ko'rish     — STAFF_VIEWERS  (HR, filial rahbari, moliya direktori)
#    tahrirlash  — STAFF_EDIT     (telefon, sana, lavozim, fiks oylik)
#    rol berish  — USER_ADMIN     (faqat asoschi, o'zgarmadi)
# =====================================================================

STAFF_EDIT = STAFF_VIEWERS

# Fiks oylikni kim o'zgartira oladi. Filial rahbari RO'YXATDA YO'Q:
# u o'z filialida to'liq huquqqa ega, lekin maosh — bu pul, va o'z
# jamoasining oyligini o'zi ko'tarib qo'yishi mumkin bo'lardi.
SALARY_EDIT = SALARY_VIEW_ALL

# HR shu rollarda yangi xodim ochadi va login/parol beradi — ya'ni
# HAMMAGA, faqat ASOSCHI va FILIAL RAHBARI bundan mustasno: ular
# tizimda to'liq huquqqa ega, ularni faqat asoschi tayinlaydi. Aks
# holda HR o'ziga filial rahbari huquqini berib olishi mumkin bo'lardi.
# DIQQAT: "Ota-ona" va "O'quvchi" ATAYLAB YO'Q (2026-08-10, Jahongir:
# "ota-ona yoki o'quvchi degan rol ochib o'tirilmasin ... bu yerda
# ota-ona o'quvchi degan rollar keremas, olib tashla").
#
# Sabab: ular XODIM emas — hisoblari QO'LDA ochilmaydi:
#   - o'quvchi: o'quvchi kartasi yaratilishi bilan hisob AVTOMAT
#     ochiladi (login = telefon raqami, parol = jonyjony);
#   - ota-ona: umuman hisob ochilmaydi, maxsus havola orqali kiradi
#     (parent_token), u ham o'quvchi kartasida avtomat turadi.
# Shuning uchun bu ikkisi xodim rollari ro'yxatida ko'rinmasligi
# kerak — aks holda HR adashib "ota-ona" hisobini ochib qo'yardi.
HR_ASSIGNABLE_ROLES = [
    TEACHER, SUPPORT_TEACHER, EXAMINER, ADMINISTRATOR,
    SALES_MANAGER, SMM_MANAGER, ACCOUNTANT, FACILITY_MANAGER,
    SALES_HEAD, ACADEMIC_HEAD, FINANCE_DIRECTOR,
    HEAD_EXAMINER, HEAD_SUPPORT, HR_MANAGER, EVENT_MANAGER,
]

# Xodim sifatida QO'LDA tayinlanadigan rollar (ota-ona/o'quvchisiz).
# Xodim kartasidagi rol tanlagichlari shu ro'yxatdan chiqadi.
STAFF_ASSIGNABLE_ROLES = [r for r in ALL_ROLES
                          if r not in (PARENT, STUDENT)]


# Filial rahbari o'z filialida shu rollarni tayinlay oladi
# Ota-ona/o'quvchi bu yerda ham YO'Q (2026-08-10) — yuqoridagi
# HR_ASSIGNABLE_ROLES izohiga qarang: ular xodim emas, hisobi
# qo'lda ochilmaydi.
BRANCH_ASSIGNABLE_ROLES = [
    SALES_MANAGER, ADMINISTRATOR, TEACHER, SUPPORT_TEACHER,
    EXAMINER,
]


def can_assign_role(requester_role: str, target_role: str) -> bool:
    """Shu rolli odam boshqasiga shu rolni bera oladimi.

    Frontenddagi assignableRoles() bilan bir xil bo'lishi shart —
    aks holda tugma ko'rinadi, lekin bosilganda 403 chiqadi."""
    if requester_role == FOUNDER:
        return True
    if requester_role == HR_MANAGER:
        return target_role in HR_ASSIGNABLE_ROLES
    if requester_role == BRANCH_MANAGER:
        return target_role in BRANCH_ASSIGNABLE_ROLES
    return False


# =====================================================================
#  DARS KO'CHIRISH (RESCHEDULE)
#
#  Nega cheklov bor: dars tez-tez surilsa o'quvchining kayfiyati
#  tushadi, darsga qiziqishi yo'qoladi va ishonch pasayadi — oxir-oqibat
#  markazdan chiqib ketish ko'payadi. Shuning uchun surish imkoni bor,
#  lekin sanoqli.
#
#  Ustoz darsni BEKOR QILA OLMAYDI — faqat boshqa kunga ko'chiradi.
#  Yangi sana ko'rsatilmasa so'rov qabul qilinmaydi.
# =====================================================================

# ERKIN SURISH OLIB TASHLANDI (2026-09-24, Jahongir: "o'qituvchilardan
# erkin darsni surishni olib tashla"). Ilgari ustoz oyiga ikki marta
# hech kimdan so'ramay dars ko'chira olardi — so'rov o'sha zahoti
# "avtomat" bo'lib kuchga kirardi. Endi ustozning HAR BIR surishi
# o'quv bo'limi tasdig'idan o'tadi. Rahbariyat (RESCHEDULE_APPROVE)
# uchun hech nima o'zgarmadi — ular avvalgidek to'g'ridan-to'g'ri
# ko'chiradi. Quyidagi sonlar saqlanib qoldi: ular endi faqat
# hisobot uchun ("shu oyda nechta surildi").
RESCHEDULE_TEACHER_AUTO = False

RESCHEDULE_PER_MONTH = 2        # oyiga avtomat ruxsat beriladigan soni
RESCHEDULE_PER_WINDOW = 12      # uzoq oynadagi umumiy chegara
RESCHEDULE_WINDOW_DAYS = 180    # 6 oy

# Foydalanilmagan surishlar keyingi oyga O'TMAYDI. Har oy nolga
# qaytadi — aks holda ustoz 6 oy yig'ib, bir oyda hammasini
# ishlatishi mumkin bo'lardi va o'quvchi uchun bu eng yomoni.
RESCHEDULE_CARRY_OVER = False

RESCHEDULE_REASONS = [
    ("sick", "Kasal bo'lib qoldim"),
    ("family", "Oilaviy sabab"),
    ("exam", "O'zimning imtihonim / o'qishim"),
    ("transport", "Yo'l / transport"),
    ("event", "Markaz tadbiri"),
    ("holiday", "Bayram / dam olish"),
    ("other", "Boshqa"),
]
RESCHEDULE_REASON_LABELS = dict(RESCHEDULE_REASONS)

RESCHEDULE_STATUSES = [
    ("auto", "Avtomat ruxsat berildi", "emerald"),
    ("pending", "Tasdiq kutilmoqda", "amber"),
    ("approved", "Tasdiqlandi", "emerald"),
    ("rejected", "Rad etildi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
RESCHEDULE_STATUS_LABELS = {k: l for k, l, _ in RESCHEDULE_STATUSES}
RESCHEDULE_STATUS_TONE = {k: t for k, _, t in RESCHEDULE_STATUSES}
RESCHEDULE_DONE = ["auto", "approved"]

# Kamida shuncha kun oldin so'ralsin — ertaga deb bugun aytish
# o'quvchi va ota-onani ogohlantirishga vaqt qoldirmaydi
RESCHEDULE_MIN_NOTICE_DAYS = 1
# Bundan uzoqqa surib bo'lmaydi
RESCHEDULE_MAX_SHIFT_DAYS = 30

# 2026-08-12, Jahongir: "HR manager yoki O'quv bo'limi rahbariga -
# ikkalasidan biriga borishi kerak" - HR ham tasdiqlay oladi.
RESCHEDULE_APPROVE = FULL_ACCESS + [ACADEMIC_HEAD, HR_MANAGER]


def reschedule_quota(used_month: int, used_window: int) -> dict:
    """Qolgan surish imkoni. Ikkita chegara ham tekshiriladi."""
    left_month = max(0, RESCHEDULE_PER_MONTH - used_month)
    left_window = max(0, RESCHEDULE_PER_WINDOW - used_window)
    return {
        "used_month": used_month,
        "used_window": used_window,
        "per_month": RESCHEDULE_PER_MONTH,
        "per_window": RESCHEDULE_PER_WINDOW,
        "window_days": RESCHEDULE_WINDOW_DAYS,
        "left_month": left_month,
        "left_window": left_window,
        # Ikkalasidan kichigi — haqiqiy qolgan imkon
        "left": min(left_month, left_window),
        # Avtomat ruxsat: ustozda o'chirilgan (2026-09-24)
        "auto_ok": (RESCHEDULE_TEACHER_AUTO
                    and left_month > 0 and left_window > 0),
        "teacher_auto": RESCHEDULE_TEACHER_AUTO,
    }


# =====================================================================
#  BOSHQA USTOZ O'RNIGA O'TISH (SUBSTITUTION)
# =====================================================================

SUBSTITUTION_STATUSES = [
    ("offered", "Taklif qilindi", "sky"),
    ("accepted", "Qabul qilindi", "emerald"),
    ("declined", "Rad etildi", "slate"),
    ("done", "O'tildi", "teal"),
    ("cancelled", "Bekor qilindi", "slate"),
]
SUB_STATUS_LABELS = {k: l for k, l, _ in SUBSTITUTION_STATUSES}
SUB_STATUS_TONE = {k: t for k, _, t in SUBSTITUTION_STATUSES}

# O'rinbosar darsi kimning ish haqiga tushadi: darsni HAQIQATDA
# o'tgan ustozga. Lesson.teacher_id shuning uchun bor.
SUBSTITUTION_MANAGE = FULL_ACCESS + [ACADEMIC_HEAD]


# =====================================================================
#  KITOB BUYURTMASI
#
#  Ustoz kitob so'raydi → so'rov filial rahbariga VAZIFA bo'lib boradi.
#  Og'zaki aytilgan iltimos yo'qoladi, vazifa yo'qolmaydi.
# =====================================================================

BOOK_ORDER_STATUSES = [
    ("new", "Yangi so'rov", "sky"),
    ("approved", "Tasdiqlandi", "emerald"),
    ("ordered", "Buyurtma berildi", "violet"),
    ("delivered", "Yetkazildi", "teal"),
    ("rejected", "Rad etildi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
BOOK_STATUS_LABELS = {k: l for k, l, _ in BOOK_ORDER_STATUSES}
BOOK_STATUS_TONE = {k: t for k, _, t in BOOK_ORDER_STATUSES}
BOOK_OPEN_STATUSES = ["new", "approved", "ordered"]

BOOK_URGENCY = [
    ("normal", "Oddiy", "slate", 7),
    ("soon", "Tez orada kerak", "amber", 3),
    ("urgent", "Shoshilinch", "red", 1),
]
BOOK_URGENCY_LABELS = {k: l for k, l, _t, _d in BOOK_URGENCY}
BOOK_URGENCY_TONE = {k: t for k, _l, t, _d in BOOK_URGENCY}
BOOK_URGENCY_DAYS = {k: d for k, _l, _t, d in BOOK_URGENCY}

BOOK_ORDER_MANAGE = FULL_ACCESS + [ACADEMIC_HEAD, FACILITY_MANAGER]


# =====================================================================
#  TAJRIBA — YILDA KO'RSATISH
# =====================================================================

def tenure_years(months: float) -> float:
    """Oydan yilga. 42 oy -> 3.5 yil."""
    return round((months or 0) / 12, 1)


def tenure_years_text(months: float) -> str:
    """Odam o'qiydigan ko'rinish. Bir yildan kam bo'lsa oyda qoladi —
    "0.3 yil" degani hech narsa anglatmaydi."""
    m = months or 0
    if m < 12:
        n = int(round(m))
        return f"{n} oy" if n else "yangi"
    y = tenure_years(m)
    return f"{y:g} yil"


# =====================================================================
#  USTOZ DASHBOARDI: KRITIK OGOHLANTIRISHLAR
#
#  Har bir ogohlantirish — bugun qilinadigan ish. Shuning uchun ular
#  "ko'rsatkich" emas, "kimga, nima qilish kerak" ko'rinishida
#  beriladi.
# =====================================================================

# Uy vazifasi holatlari
HOMEWORK_STATES = [
    (1, "Bajardi", "emerald"),
    (2, "Qisman", "amber"),
    (0, "Bajarmadi", "red"),
]
HOMEWORK_LABELS = {k: l for k, l, _ in HOMEWORK_STATES}
HOMEWORK_TONE = {k: t for k, _, t in HOMEWORK_STATES}

TEACHER_ALERTS = [
    ("absent_streak", "Ketma-ket 2 dars kelmadi", "red",
     "Ota-onasiga bugun qo'ng'iroq qiling — uchinchi darsdan keyin "
     "qaytarish ancha qiyin bo'ladi."),
    ("score_drop", "Natijasi keskin tushdi", "red",
     "Nima o'zgarganini so'rang: uyda muammo yoki mavzu tushunarsizmi."),
    ("group_attendance", "Guruh davomati 70% dan past", "amber",
     "Bitta bola emas, butun guruh — dars formatini ko'rib chiqing."),
    ("homework_drop", "Uy vazifasi topshirish foizi pasaydi", "amber",
     "Vazifa hajmi yoki tushuntirish yetarli emasligi mumkin."),
    ("no_growth", "30 kundan beri akademik o'sish yo'q", "amber",
     "Baholar joyida turibdi — mavzu qiyinlashmayaptimi yoki "
     "baholash bir xilmi?"),
    ("attendance_missing", "Dars bo'ldi, davomat belgilanmagan", "red",
     "Davomat belgilanmasa ish haqi ham hisoblanmaydi."),
]
ALERT_LABELS = {k: l for k, l, _t, _h in TEACHER_ALERTS}
ALERT_TONE = {k: t for k, _l, t, _h in TEACHER_ALERTS}
ALERT_ADVICE = {k: h for k, _l, _t, h in TEACHER_ALERTS}

# ---- Chegaralar (asoschi sozlashi mumkin) ----
ABSENT_STREAK_ALERT = 2          # ketma-ket nechta dars
GROUP_ATTENDANCE_MIN = 70.0      # guruh davomati foizi
SCORE_DROP_POINTS = 1.0          # o'rtacha baho shuncha tushsa
SCORE_DROP_WINDOW = 3            # oxirgi nechta dars solishtiriladi
HOMEWORK_DROP_PERCENT = 15.0     # foiz shuncha pasaysa
NO_GROWTH_DAYS = 30              # shuncha kun o'sish bo'lmasa
NO_GROWTH_MIN_LESSONS = 4        # xulosa uchun kamida shuncha dars
ATTENDANCE_GRACE_HOURS = 4       # darsdan keyin shuncha soat kutiladi
STUDENT_RISK_ATTENDANCE = 70.0

# Uy vazifasi bo'yicha risk. Endi haqiqiy ma'lumot bor — signal
# qo'lda emas, avtomat qo'yiladi.
HOMEWORK_RISK_PERCENT = 50.0
HOMEWORK_MIN_CHECKED = 4          # shundan kam tekshirilgan bo'lsa xulosa yo'q
HOMEWORK_GOOD_PERCENT = 80.0


def homework_band(percent: float | None) -> tuple[str, str]:
    """Uy vazifasi foizi -> (yorliq, rang)."""
    if percent is None:
        return ("Ma'lumot yo'q", "slate")
    if percent >= HOMEWORK_GOOD_PERCENT:
        return ("Yaxshi", "emerald")
    if percent >= HOMEWORK_RISK_PERCENT:
        return ("O'rtacha", "amber")
    return ("Past", "red")   # o'quvchi davomati foizi


# =====================================================================
#  IMTIHON BUYURTMASI
#
#  Ustoz imtihon o'tkazishni so'raydi, examiner qabul qiladi. Ilgari
#  ustoz imtihonni o'zi "qoralama" qilib yaratardi va examiner uni
#  ko'rishi uchun ro'yxatni ochib turishi kerak edi — ya'ni ish
#  hech kimga BORMASDAN kutib turardi. Endi so'rov filialdagi
#  examinerlarga vazifa bo'lib boradi va kim qabul qilgani ko'rinadi.
# =====================================================================
EXAM_ORDER_STATUSES = [
    ("new", "Yangi so'rov", "amber"),
    ("accepted", "Qabul qilindi", "emerald"),
    # Examiner boshqa kun/vaqt taklif qildi — ustoz javobini kutmoqda
    # (2026-10-02)
    ("reschedule", "Ko'chirish taklifi — ustoz javobi kutilmoqda", "sky"),
    ("done", "O'tkazildi", "teal"),
    ("rejected", "Rad etildi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
EXAM_ORDER_LABELS = {k: l for k, l, _t in EXAM_ORDER_STATUSES}
EXAM_ORDER_TONE = {k: t for k, _l, t in EXAM_ORDER_STATUSES}
# Examiner ko'radigan navbat
EXAM_ORDER_OPEN = ["new", "accepted", "reschedule"]

# Kim so'raydi, kim qabul qiladi
EXAM_ORDER_CREATE = [TEACHER, SUPPORT_TEACHER, ACADEMIC_HEAD] + FULL_ACCESS
EXAM_ORDER_ACCEPT = EXAM_ACCESS            # asoschi, examiner, boshliq

# Imtihon kamida shuncha kun oldin so'ralsin: examiner ham odam,
# uning ham jadvali bor
EXAM_ORDER_MIN_NOTICE_DAYS = 1
# Bundan uzoqqa buyurtma qilinmaydi — jadval o'zgarib ketadi
EXAM_ORDER_MAX_AHEAD_DAYS = 60
# Rad etish sababsiz bo'lmaydi
EXAM_ORDER_REJECT_NEEDS_NOTE = True

EXAM_ORDER_REJECT_REASONS = [
    ("busy", "Shu vaqtda band"),
    # 2026-10-02, Jahongir: "Shaxsiy sababga ko'ra, Xatolik tufayli,
    # Examiner yo'q va h.k."
    ("personal", "Shaxsiy sababga ko'ra"),
    ("mistake", "Xatolik tufayli"),
    ("no_examiner", "Examiner yo'q"),
    ("too_soon", "Juda kech so'ralgan"),
    ("not_ready", "Guruh imtihonga tayyor emas"),
    ("wrong_kind", "Test turi mos emas"),
    ("other", "Boshqa sabab"),
]

# Vaqtni ko'chirish sabablari (2026-10-02)
EXAM_ORDER_RESCHEDULE_REASONS = [
    ("personal", "Shaxsiy sababga ko'ra"),
    ("busy", "Examiner shu vaqtda band"),
    ("no_examiner", "Shu kuni examiner yo'q"),
    ("mistake", "Xatolik tufayli (vaqt noto'g'ri)"),
    ("room", "Xona bo'sh emas"),
    ("other", "Boshqa sabab"),
]


def exam_order_message(*, teacher: str, branch: str, date_text: str,
                       time_text: str, kind: str, group: str,
                       students: int, accepted_by: str | None = None,
                       status: str = "new",
                       unit_no: int | None = None) -> str:
    """Buyurtma xabari. Ustoz ham, examiner ham AYNAN bir xil matnni
    ko'radi — kim nimani ko'rgani haqida bahs chiqmaydi."""
    lines = [
        "\U0001F514 Yangi imtihon buyurtmasi",
        "",
        f"Ustoz: {teacher}",
        f"Filial: {branch}",
        f"Sana: {date_text}",
        f"Vaqt: {time_text}",
        f"Test turi: {kind}"
        + (f" — Unit {unit_no}" if unit_no else ""),
        f"Guruh: {group}",
        f"O'quvchilar soni: {students}",
    ]
    if status == "reschedule":
        lines += ["", "\U0001F553 Vaqtni ko'chirish taklif qilindi — "
                      "ustoz javobi kutilmoqda"]
    elif accepted_by:
        lines += ["", f"\u2705 Qabul qilindi: {accepted_by}"]
    elif status == "rejected":
        lines += ["", "\u274C Rad etildi"]
    elif status == "cancelled":
        lines += ["", "\U0001F6AB Bekor qilindi"]
    return "\n".join(lines)


def uz_date_full(d) -> str:
    """12-avgust 2026 ko'rinishi. uz_date() dan farqi — YIL ham bor.

    2026-08-12, Jahongir: "hamma joyda date faqat raqamda yozilgan, shu
    oylarni nomlarini yozgin chalkashlik bolmasin". 01.08 va 08.01 ni
    chalkashtirish oson — oy nomi bo'lsa xato bo'lmaydi."""
    if not d:
        return "—"
    return f"{d.day}-{UZ_MONTHS[d.month - 1]} {d.year}"


# =====================================================================
#  HR FAZA 2B — ATS QUVURI, SUHBAT VA BAHOLASH VARAQASI
#
#  Nima uchun alohida "ariza" tushunchasi kerak: bitta odam ikkita
#  vakansiyaga topshirishi mumkin (masalan ustoz va administrator).
#  Agar bosqich odamning O'ZIDA saqlansa, u ikkinchi vakansiyada ham
#  "rad etilgan" bo'lib qoladi va yaxshi nomzod behuda yo'qoladi.
# =====================================================================
APPLICATION_STAGES = [
    # (kalit, nom, rang, yopiqmi, SLA kun)
    ("new",        "Yangi ariza",            "slate",   False, 2),
    ("screening",  "Rezyume ko'rilmoqda",    "sky",     False, 3),
    ("phone",      "Telefon suhbati",        "sky",     False, 3),
    ("interview",  "Suhbat",                 "violet",  False, 5),
    ("task",       "Topshiriq berildi",      "violet",  False, 5),
    ("demo",       "Sinov darsi",            "amber",   False, 5),
    ("reference",  "Tavsiyanoma tekshiruvi", "amber",   False, 3),
    ("offer",      "Taklif berildi",         "teal",    False, 3),
    ("hired",      "Ishga olindi",           "emerald", True,  None),
    ("rejected",   "Rad etildi",             "red",     True,  None),
    ("withdrew",   "O'zi voz kechdi",        "slate",   True,  None),
    ("pool",       "Talent pool",            "indigo",  True,  None),
]
APPLICATION_LABELS = {k: l for k, l, _t, _c, _s in APPLICATION_STAGES}
APPLICATION_TONE = {k: t for k, _l, t, _c, _s in APPLICATION_STAGES}
APPLICATION_SLA = {k: s for k, _l, _t, _c, s in APPLICATION_STAGES}
APPLICATION_CLOSED = [k for k, _l, _t, c, _s in APPLICATION_STAGES if c]
APPLICATION_OPEN = [k for k, _l, _t, c, _s in APPLICATION_STAGES if not c]

# Quvur tartibi — kanban ustunlari shu ketma-ketlikda chiziladi
APPLICATION_FLOW = ["new", "screening", "phone", "interview", "task",
                    "demo", "reference", "offer", "hired"]


def application_next(stage: str) -> str | None:
    """Keyingi bosqich. Oxirgisida None."""
    if stage not in APPLICATION_FLOW:
        return None
    i = APPLICATION_FLOW.index(stage)
    return APPLICATION_FLOW[i + 1] if i + 1 < len(APPLICATION_FLOW) else None


def application_progress(stage: str) -> int:
    """Quvurning necha foizi bosib o'tilgan."""
    if stage == "hired":
        return 100
    if stage in APPLICATION_CLOSED or stage not in APPLICATION_FLOW:
        return 0
    return round(APPLICATION_FLOW.index(stage)
                 / (len(APPLICATION_FLOW) - 1) * 100)


# Rad etish sabablari. "Boshqa sabab" ataylab oxirida: statistika
# ma'noli bo'lishi uchun aniq sabab tanlanishi kerak.
REJECT_REASONS = [
    ("no_experience", "Tajribasi yetarli emas"),
    ("weak_demo", "Sinov darsi kuchsiz"),
    ("weak_language", "Til darajasi past"),
    ("salary", "Ish haqi kelishilmadi"),
    ("schedule", "Jadval to'g'ri kelmadi"),
    ("culture", "Jamoaga mos kelmadi"),
    ("no_show", "Suhbatga kelmadi"),
    ("background", "Tavsiyanoma salbiy"),
    ("other", "Boshqa sabab"),
]
REJECT_LABELS = dict(REJECT_REASONS)
# Bularda nomzod aybdor emas — keyin qaytib kelishi mumkin
POOL_WORTHY = ["salary", "schedule", "no_experience"]

# ---- Suhbat turlari ----
INTERVIEW_KINDS = [
    ("phone", "Telefon suhbati", 20),
    ("hr", "HR suhbati", 45),
    ("tech", "Kasbiy suhbat", 60),
    ("demo", "Sinov darsi", 45),
    ("final", "Yakuniy suhbat", 30),
]
INTERVIEW_KIND_LABELS = {k: l for k, l, _m in INTERVIEW_KINDS}
INTERVIEW_MINUTES = {k: m for k, _l, m in INTERVIEW_KINDS}

INTERVIEW_STATUSES = [
    ("planned", "Rejalashtirilgan", "sky"),
    ("done", "O'tkazildi", "emerald"),
    ("no_show", "Nomzod kelmadi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
INTERVIEW_STATUS_LABELS = {k: l for k, l, _t in INTERVIEW_STATUSES}
INTERVIEW_STATUS_TONE = {k: t for k, _l, t in INTERVIEW_STATUSES}

# ---- Baholash varaqasi: 15 kompetensiya, og'irlik bilan ----
#      (kalit, nom, guruh, og'irlik)
COMPETENCIES = [
    ("subject",       "Fanni bilishi",              "kasbiy",    3),
    ("method",        "Metodika va dars qurilishi", "kasbiy",    3),
    ("language",      "Til darajasi",               "kasbiy",    3),
    ("tech",          "Texnika bilan ishlashi",     "kasbiy",    1),
    ("planning",      "Rejalashtirish",             "kasbiy",    2),
    ("communication", "Muloqot",                    "shaxsiy",   3),
    ("empathy",       "Bolani tushunishi",          "shaxsiy",   3),
    ("discipline",    "Intizom va punktuallik",     "shaxsiy",   3),
    ("teamwork",      "Jamoada ishlashi",           "shaxsiy",   2),
    ("stress",        "Bosim ostida ishlashi",      "shaxsiy",   2),
    ("learning",      "O'rganishga ochiqligi",      "salohiyat", 3),
    ("feedback",      "Fikrni qabul qilishi",       "salohiyat", 3),
    ("initiative",    "Tashabbuskorligi",           "salohiyat", 2),
    ("growth",        "O'sish istagi",              "salohiyat", 2),
    ("values",        "Qadriyatlarga mosligi",      "salohiyat", 3),
]
COMPETENCY_LABELS = {k: l for k, l, _g, _w in COMPETENCIES}
COMPETENCY_GROUP = {k: g for k, _l, g, _w in COMPETENCIES}
COMPETENCY_WEIGHT = {k: w for k, _l, _g, w in COMPETENCIES}
COMPETENCY_GROUPS = [
    ("kasbiy", "Kasbiy tayyorgarlik"),
    ("shaxsiy", "Shaxsiy fazilatlar"),
    ("salohiyat", "O'sish salohiyati"),
]
# Har kompetensiya 1-5 ball
SCORE_MIN, SCORE_MAX = 1, 5
SCORE_LABELS = {
    1: "Umuman yo'q",
    2: "Zaif",
    3: "Yetarli",
    4: "Yaxshi",
    5: "A'lo",
}

# Yakuniy tavsiya
RECOMMENDATIONS = [
    ("strong_yes", "Albatta olamiz", "emerald", 2),
    ("yes", "Olsa bo'ladi", "teal", 1),
    ("maybe", "Ikkilanaman", "amber", 0),
    ("no", "Olmaymiz", "orange", -1),
    ("strong_no", "Umuman mos emas", "red", -2),
]
RECOMMENDATION_LABELS = {k: l for k, l, _t, _v in RECOMMENDATIONS}
RECOMMENDATION_TONE = {k: t for k, _l, t, _v in RECOMMENDATIONS}
RECOMMENDATION_VALUE = {k: v for k, _l, _t, v in RECOMMENDATIONS}

SCORECARD_PASS = 70.0        # foizda


def scorecard_percent(scores: dict) -> float | None:
    """Og'irlikli o'rtacha.

    Baholanmagan kompetensiya hisobga KIRMAYDI — aks holda yarim
    to'ldirilgan varaqa past foiz ko'rsatib, yaxshi nomzodni behuda
    yo'qotardi."""
    num = den = 0.0
    for k, v in (scores or {}).items():
        w = COMPETENCY_WEIGHT.get(k)
        if not w or v is None:
            continue
        num += float(v) * w
        den += SCORE_MAX * w
    return round(num / den * 100, 1) if den else None


def scorecard_band(percent) -> tuple:
    if percent is None:
        return ("To'ldirilmagan", "slate")
    if percent >= 85:
        return ("Kuchli nomzod", "emerald")
    if percent >= SCORECARD_PASS:
        return ("Mos keladi", "teal")
    if percent >= 55:
        return ("Chegarada", "amber")
    return ("Mos emas", "red")


# ---- Savollar bankisi: (kompetensiya, savol) ----
QUESTION_BANK = [
    ("method", "Bolalar darsni tushunmayotganini qanday bilasiz?"),
    ("method", "Bitta mavzuni ikki xil usulda tushuntirib bering."),
    ("subject", "Present Perfect va Past Simple farqini bolaga qanday "
                "tushuntirasiz?"),
    ("language", "O'zingizni qanday darajada baholaysiz va nima "
                 "asosida?"),
    ("empathy", "Darsda yig'lab yuborgan bola bilan nima qilasiz?"),
    ("empathy", "Sekin o'zlashtiruvchi bolaga qanday yondashasiz?"),
    ("discipline", "Kechikib qolgan holatingiz bo'lganmi? Nima "
                   "qilgansiz?"),
    ("discipline", "Guruhda tartib buzilsa nima qilasiz?"),
    ("communication", "Norozi ota-ona bilan suhbatni qanday "
                      "boshlaysiz?"),
    ("teamwork", "Hamkasbingiz bilan kelisha olmasangiz nima qilasiz?"),
    ("stress", "Bir vaqtda ikki muhim ish chiqsa qaysinisini tanlaysiz "
               "va nega?"),
    ("feedback", "Sizga oxirgi marta qachon tanqid aytilgan va siz nima "
                 "qilgansiz?"),
    ("learning", "Oxirgi yarim yilda nima yangi narsa o'rgandingiz?"),
    ("initiative", "O'zingiz boshlab qilgan ishingizni ayting."),
    ("growth", "Uch yildan keyin o'zingizni qayerda ko'rasiz?"),
    ("values", "Sizningcha yaxshi ustoz nima bilan farq qiladi?"),
    ("planning", "Bir oylik dars rejasini qanday tuzasiz?"),
    ("tech", "Onlayn dars o'tganmisiz? Qanday vositalardan "
             "foydalangansiz?"),
]

# Ruxsatlar
ATS_VIEW = HR_FULL + [ACADEMIC_HEAD, BRANCH_MANAGER]
ATS_MANAGE = HR_FULL + [ACADEMIC_HEAD]
# Suhbat o'tkazuvchi kim bo'lishi mumkin
INTERVIEWERS = ATS_MANAGE + [BRANCH_MANAGER, HEAD_EXAMINER, EXAMINER]

# Dublikat nomzodni topish oynasi
DUPLICATE_DAYS = 365


def normalize_phone(phone):
    """TELEFONNI BITTA FORMATGA KELTIRISH (2026-09-16).

    Bazada raqamlar aralash yotardi: "+998 90 123-45-67", "998901234567",
    "901234567". Sayt (PhoneInput) esa 9 raqamni saqlaydi va chiroyli
    ko'rsatadi. Endi hamma joyda shu bitta qoida:
      - O'zbekiston raqami -> 9 raqam: "901234567";
      - boshqa davlat yoki tushunarsiz qiymat -> O'ZGARTIRILMAYDI
        (ma'lumot yo'qolmasin);
      - bo'sh qiymat -> None."""
    if phone is None:
        return None
    s = str(phone).strip()
    if not s:
        return None
    d = "".join(ch for ch in s if ch.isdigit())
    if len(d) == 12 and d.startswith("998"):
        return d[3:]
    if len(d) == 9 and not s.lstrip().startswith("+"):
        return d
    if len(d) == 9 and s.lstrip().startswith("+998"):
        return d
    return s


def phone_login(phone):
    """Telefondan login yasash (o'quvchi hisobi) — (login, band_tekshiruv).

    Telefon bazada 9 raqam bo'lib turadi (normalize_phone), lekin
    o'quvchi loginlari tarixan "998901234567" ko'rinishida ochilgan.
    Bir odamga ikkinchi hisob ochilib qolmasligi uchun login doim
    "998..." bo'ladi va bandlik IKKALA ko'rinish bo'yicha tekshiriladi.
    Kirishda ikkalasi ham qabul qilinadi (auth_users.login)."""
    d = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if len(d) == 12 and d.startswith("998"):
        d = d[3:]
    if len(d) == 9:
        login = "998" + d
        return login, {login, d}
    if len(d) >= 7:
        return d, {d}
    return None, set()


def phone_key(phone) -> str:
    """Telefonni solishtirish uchun raqamga keltiradi: +998 90 123-45-67
    va 901234567 bir xil odam."""
    return "".join(ch for ch in (phone or "") if ch.isdigit())[-9:]


# =====================================================================
#  HR FAZA 2C — TAKLIF (OFFER)
#
#  Taklif og'zaki emas, yozma bo'ladi va tasdiq zanjiridan o'tadi:
#  HR tuzadi → rahbariyat tasdiqlaydi → nomzodga yuboriladi →
#  nomzod javob beradi. Har o'zgartirish yangi VERSIYA — kim qachon
#  qancha taklif qilgani hech qachon yo'qolmaydi.
# =====================================================================
OFFER_STATUSES = [
    ("draft",    "Qoralama",             "slate"),
    ("approval", "Tasdiq kutmoqda",      "amber"),
    ("approved", "Tasdiqlandi",          "sky"),
    ("sent",     "Nomzodga yuborildi",   "violet"),
    ("accepted", "Nomzod qabul qildi",   "emerald"),
    ("declined", "Nomzod rad etdi",      "red"),
    ("expired",  "Muddati o'tdi",        "slate"),
    ("withdrawn", "Qaytarib olindi",     "slate"),
]
OFFER_LABELS = {k: l for k, l, _t in OFFER_STATUSES}
OFFER_TONE = {k: t for k, _l, t in OFFER_STATUSES}
OFFER_OPEN = ["draft", "approval", "approved", "sent"]
OFFER_FINAL = ["accepted", "declined", "expired", "withdrawn"]

# Kim tuzadi, kim tasdiqlaydi. Taklifda PUL bor — tasdiqsiz chiqmaydi.
OFFER_CREATE = HR_FULL
OFFER_APPROVE = [FOUNDER, FINANCE_DIRECTOR, PARTNER_HEAD]
# Nomzod javobini kutish muddati
OFFER_VALID_DAYS = 5


def offer_next(status: str, action: str) -> str | None:
    """Ruxsat etilgan o'tishlar. Chetlab o'tish yo'q: qoralama
    to'g'ridan-to'g'ri "qabul qilindi" bo'la olmaydi."""
    allowed = {
        ("draft", "submit"): "approval",
        ("approval", "approve"): "approved",
        ("approval", "reject"): "draft",
        ("approved", "send"): "sent",
        ("sent", "accept"): "accepted",
        ("sent", "decline"): "declined",
        ("sent", "expire"): "expired",
        ("draft", "withdraw"): "withdrawn",
        ("approval", "withdraw"): "withdrawn",
        ("approved", "withdraw"): "withdrawn",
        ("sent", "withdraw"): "withdrawn",
    }
    return allowed.get((status, action))


# =====================================================================
#  HR FAZA 3 — XODIM HAYOTIY SIKLI
#  Hujjatlar (muddati bilan), onboarding, sinov muddati, ta'til.
# =====================================================================
DOCUMENT_KINDS = [
    ("passport", "Pasport / ID karta", True),
    ("diploma", "Diplom", False),
    ("certificate", "Sertifikat (IELTS, CEFR...)", True),
    ("contract", "Mehnat shartnomasi", True),
    ("medical", "Tibbiy ma'lumotnoma", True),
    ("photo", "3x4 surat", False),
    ("reference", "Tavsiyanoma", False),
    ("other", "Boshqa", False),
]
DOCUMENT_LABELS = {k: l for k, l, _e in DOCUMENT_KINDS}
# Muddati bo'ladigan hujjatlar — tugashidan oldin ogohlantiriladi
DOCUMENT_EXPIRES = [k for k, _l, e in DOCUMENT_KINDS if e]
DOCUMENT_WARN_DAYS = 30

# Onboarding allaqachon mavjud (ONBOARDING_STEPS yuqorida, 26-partiyada qurilgan).

# Sinov muddati nazorati: har oy alohida xulosa
PROBATION_DECISIONS = [
    ("on_track", "Yaxshi ketmoqda", "emerald"),
    ("watch", "E'tibor kerak", "amber"),
    ("risk", "Xavf ostida", "red"),
    ("passed", "Sinovdan o'tdi", "teal"),
    ("failed", "Sinovdan o'tmadi", "red"),
]
PROBATION_LABELS = {k: l for k, l, _t in PROBATION_DECISIONS}
PROBATION_TONE = {k: t for k, _l, t in PROBATION_DECISIONS}
PROBATION_FINAL = ["passed", "failed"]

# Ta'til turlari: (kalit, nom, haqlimi, yillik chegara kun)
LEAVE_KINDS = [
    ("annual", "Yillik ta'til", True, 21),
    ("sick", "Kasallik", True, None),
    ("unpaid", "Ta'tilsiz (o'z hisobidan)", False, 30),
    ("family", "Oilaviy sabab", False, 5),
    ("study", "O'qish / imtihon", False, 10),
]
LEAVE_LABELS = {k: l for k, l, _p, _d in LEAVE_KINDS}
LEAVE_PAID = {k: p for k, _l, p, _d in LEAVE_KINDS}
LEAVE_LIMIT = {k: d for k, _l, _p, d in LEAVE_KINDS}

LEAVE_STATUSES = [
    ("pending", "Kutilmoqda", "amber"),
    ("approved", "Tasdiqlandi", "emerald"),
    ("rejected", "Rad etildi", "red"),
    ("cancelled", "Bekor qilindi", "slate"),
]
LEAVE_STATUS_LABELS = {k: l for k, l, _t in LEAVE_STATUSES}
LEAVE_STATUS_TONE = {k: t for k, _l, t in LEAVE_STATUSES}
LEAVE_MIN_NOTICE_DAYS = 3          # kasallikdan tashqari
LEAVE_APPROVE = HR_FULL + [BRANCH_MANAGER]

LIFECYCLE_VIEW = HR_FULL + [BRANCH_MANAGER]

# =====================================================================
#  HR FAZA 4 — PERFORMANCE
#  Baholash yakunlangach QULFLANADI: tarix qayta yozilmaydi.
# =====================================================================
REVIEW_CRITERIA = [
    ("results", "Ish natijalari", 3),
    ("quality", "Sifat va mas'uliyat", 3),
    ("discipline", "Intizom", 2),
    ("teamwork", "Jamoa bilan ishlash", 2),
    ("growth", "O'sish va tashabbus", 2),
]
REVIEW_LABELS = {k: l for k, l, _w in REVIEW_CRITERIA}
REVIEW_WEIGHT = {k: w for k, _l, w in REVIEW_CRITERIA}


def review_percent(scores: dict):
    """1-5 balldan og'irlikli foiz. Baholanmagani hisobga kirmaydi."""
    num = den = 0.0
    for k, v in (scores or {}).items():
        w = REVIEW_WEIGHT.get(k)
        if not w or v is None:
            continue
        num += float(v) * w
        den += 5 * w
    return round(num / den * 100, 1) if den else None


ONE_ON_ONE_PRIVACY = [
    ("open", "Ochiq — HR ko'radi"),
    ("private", "Maxfiy — faqat ikkalasi"),
]
PIP_STATUSES = [
    ("active", "Faol", "amber"),
    ("passed", "Muvaffaqiyatli yakunlandi", "emerald"),
    ("failed", "Natija bermadi", "red"),
]
PIP_LABELS = {k: l for k, l, _t in PIP_STATUSES}

# =====================================================================
#  HR FAZA 5 — MUNOSABATLAR VA KETISH
# =====================================================================
DISCIPLINE_KINDS = [
    ("verbal", "Og'zaki ogohlantirish"),
    ("written", "Yozma ogohlantirish"),
    ("final", "Oxirgi ogohlantirish"),
]
DISCIPLINE_LABELS = dict(DISCIPLINE_KINDS)

RECOGNITION_KINDS = [
    ("thanks", "Rahmatnoma"),
    ("bonus", "Mukofot"),
    ("star", "Oy xodimi"),
]
RECOGNITION_LABELS = dict(RECOGNITION_KINDS)

# Ketish sabablari — "biznesga bog'liq"lari alohida: ular ustidan
# ishlash mumkin, qolganlari ustidan yo'q
EXIT_REASONS = [
    ("salary", "Ish haqidan norozi", True),
    ("management", "Rahbariyatdan norozi", True),
    ("workload", "Ish yuki og'ir", True),
    ("growth", "O'sish imkoni yo'q deb bildi", True),
    ("relocation", "Ko'chib ketdi", False),
    ("family", "Oilaviy sabab", False),
    ("study", "O'qishga ketdi", False),
    ("competitor", "Boshqa markazga o'tdi", True),
    ("dismissed", "Ishdan bo'shatildi", False),
    ("other", "Boshqa", False),
]
EXIT_LABELS = {k: l for k, l, _o in EXIT_REASONS}
EXIT_OURS = [k for k, _l, o in EXIT_REASONS if o]

OFFBOARD_STEPS = [
    ("notice", "Ariza qabul qilindi"),
    ("handover", "Ishlarni topshirish"),
    ("groups", "Guruhlarni boshqa ustozga o'tkazish"),
    ("assets", "Mulk va kitoblarni qaytarish"),
    ("account", "Hisobni o'chirish"),
    ("exit_interview", "Chiqish suhbati"),
    ("final_pay", "Yakuniy hisob-kitob"),
]
OFFBOARD_LABELS = dict(OFFBOARD_STEPS)


# =====================================================================
#  SUPPORT TEACHER OYLIGI — asoschi formulasi
#
#  Support teacher har darsini o'zi kiritadi: qaysi guruh, soat
#  nechida boshlab nechida tugatgani, nechta o'quvchi. Oy yakunida:
#
#    oylik = (soatlar x 0.30
#             + o'quvchi-soni yig'indisi x 0.20
#             + test koeffitsiyenti x 0.50) x 10 000
#
#  Test koeffitsiyenti — shu oyda dars o'tgan guruhlarining o'rtacha
#  test foizidan jadval bo'yicha olinadi. Natija 400 000 dan kam
#  bo'lsa 400 000, 1 500 000 dan ko'p bo'lsa 1 500 000 to'lanadi.
# =====================================================================
SUPPORT_PAY_MIN = 400_000
SUPPORT_PAY_MAX = 1_500_000
SUPPORT_PAY_UNIT = 10_000
SUPPORT_HOURS_W = 0.30
# YAKKA ISH (2026-09-23, Jahongir). Orqada qolgan o'quvchi bilan
# bittalab ishlash guruh bilan ishlashdan to'rt barobar kam pul
# berardi (1 soat, 1 o'quvchi = 5 000 so'm), shuning uchun support
# bunday ishni olishdan manfaatdor emas edi. Endi 1-3 o'quvchili
# seansda soat ikki barobar ball beradi. Hisob HAR SEANS uchun
# alohida yuritiladi: oy yakunidagi jami o'quvchi soniga qarab emas.
SUPPORT_SMALL_MAX = 3
SUPPORT_HOURS_W_SMALL = 0.60
# Yakka dars o'quvchilar bo'yicha ham 3 kishilik darsdek sanaladi
# (2026-09-23, Jahongir: "individual yoki qo'shimcha biriktirganda
# 3ta o'quvchiga dars o'tgandek bo'lsin"). Hisobotda o'quvchi soni
# o'zgarmaydi - faqat oylik shunday hisoblanadi.
SUPPORT_SOLO_AS_STUDENTS = 3
SUPPORT_STUDENTS_W = 0.20
SUPPORT_RESULT_W = 0.50

# (dan, gacha, koeffitsiyent) — foiz yuqori chegara KIRADI
SUPPORT_RESULT_BANDS = [
    (0, 65, 0.5),
    (66, 70, 0.6),
    (71, 76, 0.75),
    (77, 82, 0.9),
    (83, 87, 1.0),
    (88, 93, 1.15),
    (94, 97, 1.3),          # asoschi jadvalida 93 ikki qatorda edi —
    #                         88-93 pastkisiga olindi
    (98, 100, 1.5),
]

# Bitta seans uchun aql chegaralari — xato kiritishdan himoya
# SUPPORT SEANSI QOIDASI (2026-08-10, Jahongir aniqlashtirdi):
# bitta seans KAMIDA 1 soat, KO'PI BILAN 3 soat. Support qancha dars
# o'tganini O'ZI belgilaydi — soatni ro'yxatdan tanlaydi, tugash
# vaqtini hisoblab o'tirmaydi.
SUPPORT_SESSION_MIN_HOURS = 1
SUPPORT_SESSION_MAX_HOURS = 3
# Tanlash uchun tayyor qadamlar (yarim soatlik)
SUPPORT_SESSION_HOUR_STEPS = [1, 1.5, 2, 2.5, 3]
SUPPORT_SESSION_MAX_STUDENTS = 40


def support_result_coef(percent) -> float:
    """O'rtacha test foizi -> koeffitsiyent. Ma'lumot bo'lmasa eng
    pastki koeffitsiyent — natija ko'rsatilmagan ish mukofotlanmaydi."""
    if percent is None:
        return SUPPORT_RESULT_BANDS[0][2]
    p = round(float(percent))
    for lo, hi, k in SUPPORT_RESULT_BANDS:
        if lo <= p <= hi:
            return k
    return SUPPORT_RESULT_BANDS[0][2] if p < 0 \
        else SUPPORT_RESULT_BANDS[-1][2]


def support_hours_points(hours: float, students: int) -> float:
    """Bitta seansning soat ballari. 1-3 o'quvchi bo'lsa ikki barobar."""
    w = (SUPPORT_HOURS_W_SMALL
         if 0 < (students or 0) <= SUPPORT_SMALL_MAX else SUPPORT_HOURS_W)
    return round(float(hours or 0) * w, 2)


def support_salary(hours: float, students: int, percent,
                   minus: float = 0.0,
                   hours_points: float | None = None,
                   students_points: float | None = None) -> dict:
    """Formula bitta joyda — kartada ham, ro'yxatda ham, testda ham
    aynan shu hisob.

    minus — HR ayirgan jarima ballari (SupportAdjustment). Ball
    oylikka aylantirilishidan OLDIN ayiriladi, examinerdagi kabi."""
    coef = support_result_coef(percent)
    # hours_points berilsa — u seanslar bo'yicha alohida hisoblangan
    # (yakka darslar qimmatroq). Berilmasa — eski, oddiy hisob.
    h_part = (round(hours * SUPPORT_HOURS_W, 2) if hours_points is None
              else round(float(hours_points), 2))
    s_part = (round(students * SUPPORT_STUDENTS_W, 2)
              if students_points is None
              else round(float(students_points) * SUPPORT_STUDENTS_W, 2))
    r_part = round(coef * SUPPORT_RESULT_W, 2)
    gross = round(h_part + s_part + r_part, 2)
    minus = round(max(0.0, float(minus or 0)), 2)
    net = round(max(0.0, gross - minus), 2)
    raw = round(net * SUPPORT_PAY_UNIT, 0)
    clamped = min(max(raw, SUPPORT_PAY_MIN), SUPPORT_PAY_MAX)
    return {
        "hours": round(hours, 2),
        "students": students,
        "avg_percent": (round(float(percent), 1)
                        if percent is not None else None),
        "coef": coef,
        "hours_part": h_part,
        "students_part": s_part,
        "result_part": r_part,
        "gross_points": gross,
        "adjustment_points": minus,
        "points": net,
        "raw": raw,
        "salary": clamped,
        "clamped_min": raw < SUPPORT_PAY_MIN,
        "clamped_max": raw > SUPPORT_PAY_MAX,
    }


def hhmm_minutes(t: str):
    """"14:30" -> 870. Noto'g'ri format -> None."""
    try:
        h, m = str(t).strip().split(":")
        h, m = int(h), int(m)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return h * 60 + m
    except (ValueError, AttributeError):
        return None


# ------------------------------------------------------- Examiner oyligi ----
# Asoschi jadvali — "Examlar kesimida oylik chiqarish tartibi".
# Har o'tkazilgan imtihon ball beradi: imtihonning o'zi uchun +
# har qatnashgan o'quvchi uchun. Oy yakunida:
#     oylik = jami ball x 1 000 so'm   (600 ball -> 600 000 so'm)
# kamida 400 000, ko'pi bilan 1 500 000 so'm.
EXAMINER_PAY_MIN = 400_000
EXAMINER_PAY_MAX = 1_500_000
EXAMINER_PAY_UNIT = 1_000

# daraja -> (imtihon balli, har o'quvchi balli)
EXAMINER_EXAM_POINTS = {
    "step1": (11.0, 1.5),
    "step2": (13.0, 2.5),
    "step3": (15.0, 3.0),
    "mid":   (20.0, 3.5),
    "end":   (25.0, 3.5),
}

# Bajarilmagan ish uchun jarima ballari:
# daraja -> (LC UP, Coin, jadval kechikishi HAR SOATIGA)
EXAMINER_PENALTIES = {
    "step1": (3.0, 4.0, 5.0),
    "step2": (5.0, 6.0, 7.0),
    "step3": (7.0, 8.0, 9.0),
    "mid":   (10.0, 13.0, 15.0),
    "end":   (10.0, 13.0, 15.0),
}

EXAMINER_TIER_LABELS = {
    "step1": "Step 1.0",
    "step2": "Step 2.0",
    "step3": "Step 3.0",
    "mid": "Mid-course / Retake",
    "end": "End of course / Retake",
}

# Jarima qo'yish va qo'lda ball ayirish — bo'lim boshliqlari
# (Exam, HR, O'quv bo'limi) va asoschi. ESLATMAdagi qoida.
EXAMINER_PENALTY_SET = [FOUNDER, HEAD_EXAMINER, HR_MANAGER, ACADEMIC_HEAD]
# Support teacherdan jarima ball ayirish (2026-09-16, Jahongir: "HR
# uchun ham examiner ham supportlardan ayirish uchun jarima ball
# bo'limi"). Examinerlar boshlig'i supportga tegmaydi.
SUPPORT_PENALTY_SET = [FOUNDER, HR_MANAGER]
# Barcha examinerlar ro'yxatini kim ko'radi
EXAMINER_SALARY_VIEW = list(dict.fromkeys(
    SALARY_VIEW_ALL + [ACADEMIC_HEAD, HEAD_EXAMINER]))


def examiner_tier(kind, level):
    """Imtihon jadvalning qaysi qatoriga tushadi.

    Unit test — guruh darajasiga qarab (Step 1/2/3). Jadvalda
    bo'lmagan yuqori daraja (Step 4, IELTS, CEFR) unit testlari
    eng yaqin qator — Step 3.0 bo'yicha to'lanadi. Mid/End (retake
    ham) darajadan qat'i nazar o'z qatori bo'yicha. Mock jadvalda
    yo'q — ball bermaydi."""
    if kind in ("mid", "end"):
        return kind
    if kind == "unit":
        return level if level in ("step1", "step2", "step3") else "step3"
    return None


def examiner_exam_points(kind, level, students: int):
    """Bitta imtihon uchun ball: baza + o'quvchi soni x koeffitsiyent."""
    tier = examiner_tier(kind, level)
    if tier is None:
        return None
    base, per = EXAMINER_EXAM_POINTS[tier]
    return {
        "tier": tier,
        "tier_label": EXAMINER_TIER_LABELS[tier],
        "base": base,
        "per_student": per,
        "students": int(students or 0),
        "points": round(base + per * int(students or 0), 2),
    }


def examiner_exam_code(kind, level, unit_no=None, retake=False) -> str:
    """Examiner jadvalidagi qisqa nom (2026-10-02): "S2 U9", "S1 U7",
    "MID-COURSE", "END-COURSE", "MOCK". Retake — oldiga "RETAKE"."""
    if kind == "unit":
        lv = {"step1": "S1", "step2": "S2", "step3": "S3",
              "step4": "S4"}.get(level or "", (level or "").upper())
        code = f"{lv} U{unit_no}".strip() if unit_no else (lv or "UNIT")
    elif kind == "mid":
        code = "MID-COURSE"
    elif kind == "end":
        code = "END-COURSE"
    elif kind == "mock":
        code = "MOCK"
    else:
        code = (kind or "").upper()
    return f"RETAKE {code}" if retake else code


def examiner_penalty_points(kind, level, lc_up: bool, coin: bool,
                            delay_hours: float = 0.0) -> float:
    """Bitta imtihon uchun jarima ballari (musbat son qaytadi)."""
    tier = examiner_tier(kind, level)
    if tier is None:
        return 0.0
    p_lc, p_coin, p_hour = EXAMINER_PENALTIES[tier]
    total = 0.0
    if lc_up:
        total += p_lc
    if coin:
        total += p_coin
    total += p_hour * max(0.0, float(delay_hours or 0))
    return round(total, 2)


def examiner_salary(points: float) -> dict:
    """Oy yakuni: ball x 1 000 so'm, 400 000 — 1 500 000 chegarada."""
    pts = round(float(points or 0), 2)
    raw = round(pts * EXAMINER_PAY_UNIT, 0)
    salary = min(max(raw, EXAMINER_PAY_MIN), EXAMINER_PAY_MAX)
    return {
        "points": pts,
        "raw": raw,
        "salary": salary,
        "min": EXAMINER_PAY_MIN,
        "max": EXAMINER_PAY_MAX,
        "unit": EXAMINER_PAY_UNIT,
        "clamped_min": raw < EXAMINER_PAY_MIN,
        "clamped_max": raw > EXAMINER_PAY_MAX,
    }


# ------------------------------------------------- Yillik Reja / Fakt ----
# Rahbarning bosh jadvali. O'quv yili SENTABRdan boshlanadi.
# Reja oy kesimida kiritiladi; hafta/kun rejasi oydan avtomat
# taqsimlanadi (ish kunlariga bo'lib; yakshanba dam). Fakt platforma
# ma'lumotlaridan o'zi to'ladi.
# Marketolog SOTUV BONUSI shkalasi (Jahongir, 2026-08-11, Bekobod 1
# marketologi uchun berilgan jadval - barcha marketologlarga amal
# qiladi). (min_foiz, bonus_som, holat nomi) - yuqoridan pastga.
SMM_SALES_BONUS = [
    (150.0, 8_000_000, "Maksimal tushum"),
    (120.0, 5_500_000, "Rekord sotuv"),
    (110.0, 4_000_000, "Yuqori tushum"),
    (100.0, 3_000_000, "Sotuv rejasi bajarildi"),
    (90.0, 2_000_000, "Yaxshi sotuv"),
    (80.0, 1_000_000, "Minimal chiziq"),
]


def smm_sales_bonus(percent: float) -> tuple:
    """Foizdan (bonus, holat nomi). 80% dan past - bonus yo'q."""
    for mn, bonus, label in SMM_SALES_BONUS:
        if percent >= mn:
            return bonus, label
    return 0, "Sotuv rejasi bajarilmadi"


PLAN_METRICS = [
    # (kalit, nomi, bo'lim, tur: flow|stock|money, fakt avtomatmi)
    ("leads", "Lid", "online", "flow", True),
    # 2026-08-11 (Jahongir): "Onlinedan tashriflar soni" va "Yangi
    # to'lovlar soni (online)" UMUMAN olib tashlandi - fakti avtomat
    # yig'ilmasdi, hech kimga kerak emas edi (asoschiga ham).
    # O'rniga SMM'ga sotuvdagi new_payments va students ko'rinadi
    # (PLAN_SMM_EXTRA).
    ("visits", "Tashrif", "sotuv", "flow", True),
    ("new_payments", "Yangi to'lovlar soni", "sotuv", "flow", True),
    ("old_payments", "Eski to'lovlar soni", "sotuv", "flow", True),
    ("students", "O'qiyotgan o'quvchilar soni", "sotuv", "stock", True),
    ("revenue", "Yalpi tushum", "moliya", "money", True),
    ("expenses", "Xarajatlar", "moliya", "money", True),
    ("profit", "Foyda", "moliya", "money", True),
]
PLAN_METRIC_KEYS = [k for k, *_ in PLAN_METRICS]
PLAN_SECTION_LABELS = {"online": "Online", "sotuv": "Sotuv",
                       "moliya": "Moliya"}
# Bo'lim kimga ko'rinadi — "kerakli qism kerakli xodimga"
PLAN_SECTION_ROLES = {
    "online": [FOUNDER, SMM_MANAGER],
    "sotuv": [FOUNDER, SALES_HEAD, SALES_MANAGER, BRANCH_MANAGER],
    "moliya": [FOUNDER, FINANCE_DIRECTOR],
}
# SMM o'z bo'limidan tashqari shu ikki ko'rsatkichni ham ko'radi:
# yangi to'lovlar soni va o'qiyotgan o'quvchilar soni (Jahongir,
# 2026-08-11: "yangi to'lovni ozi va o'quvchi soni reja fakt
# korinsin SMM chilarda")
PLAN_SMM_EXTRA = ("new_payments", "students")

PLAN_EDIT = [FOUNDER, PARTNER_HEAD]
PLAN_VIEW = list(dict.fromkeys(
    r for rs in PLAN_SECTION_ROLES.values() for r in rs))
# O'quv yili oylari tartibi va choraklar
PLAN_MONTHS = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]
PLAN_QUARTERS = [PLAN_MONTHS[0:3], PLAN_MONTHS[3:6],
                 PLAN_MONTHS[6:9], PLAN_MONTHS[9:12]]
PLAN_DEFAULT_GROWTH = 15   # o'tgan yil faktiga +15% taklif


def plan_year_label(y: int) -> str:
    return f"{y}-{y + 1} o'quv yili"


def plan_month_year(start_year: int, month: int) -> int:
    """Sentabr-dekabr — boshlanish yili, yanvar-avgust — keyingi yil."""
    return start_year if month >= 9 else start_year + 1


def plan_sections_for(role: str):
    return [s for s, rs in PLAN_SECTION_ROLES.items() if role in rs]


# --------------------------------------------- Zararsizlik nuqtasi ----
# Xarajat guruhi tasnifi:
#   o'zgarmas  — markaz umuman ishlamasa ham to'lanadi
#   o'zgaruvchan — o'quvchi soniga qarab o'sadi (+ ustozlar ish haqi,
#                  u har doim o'zgaruvchan: dars bo'lmasa to'lanmaydi)
EXPENSE_FIXED_GROUPS = ["rent", "communal", "admin_salary", "tax"]


def expense_is_fixed(category: str) -> bool:
    return EXPENSE_CATEGORY_GROUP.get(category, "other") in \
        EXPENSE_FIXED_GROUPS


# ------------------------------------------------ Budjet va kalendar ----
BUDGET_EDIT = [FOUNDER, FINANCE_DIRECTOR, PARTNER_HEAD]
PAYMENT_DUE_KINDS = [
    ("salary", "Maosh"),
    ("rent", "Ijara"),
    ("tax", "Soliq"),
    ("ads", "Reklama to'lovi"),
    ("supplier", "Yetkazib beruvchi"),
    ("other", "Boshqa"),
]
PAYMENT_DUE_LABELS = {k: l for k, l in PAYMENT_DUE_KINDS}
# Bo'lim (departament) — xarajat guruhidan (budjet uchun)
BUDGET_DEPARTMENT_LABELS = {
    "rent": "Ijara", "communal": "Kommunal", "office": "Ofis",
    "household": "Xo'jalik", "admin_salary": "Ma'muriyat",
    "marketing": "Marketing",
    "tax": "Soliq", "other": "Boshqa",
    "teacher_payroll": "O'quv bo'limi (ustozlar)",
}


# ------------------------------------------- Muzlatish va support yo'li ----
# O'quvchini muzlatish/faollashtirish/ko'chirish — faqat shu rollar.
# Ustoz va support teacher BUNDAY amallarni qila olmaydi.
FREEZE_ROLES = [FOUNDER, SALES_MANAGER, ACADEMIC_HEAD, BRANCH_MANAGER]
# Arxivdagi o'quvchini qayta tiklash — administrator ham (2026-09-16,
# Jahongir: "Arxivdagi o'quvchilarni qayta tiklashni administratorlarga
# ochib ber"). Faqat o'z filialidagini.
STUDENT_RESTORE = FREEZE_ROLES + [ADMINISTRATOR]
# O'quvchini boshqa guruhga (shu jumladan BOSHQA FILIALDAGI guruhga)
# o'tkazish — administrator ham (2026-09-23, Jahongir: "boshqa guruhga
# otkiza olish kerak boshqa filialdagi"). Faqat O'Z filialidagi
# o'quvchini: manba _get_student_in_scope orqali tekshiriladi.
STUDENT_TRANSFER = FREEZE_ROLES + [ADMINISTRATOR]
# Yangi o'quvchi FAQAT liddan qo'shiladi (2026-09-16, Jahongir:
# "oquvchini qoshish mumkin bolmasin faqat liddan qoshish mumkin
# bo'lsin"). To'g'ridan-to'g'ri qo'shish — faqat asoschi (favqulodda).
STUDENT_CREATE = [FOUNDER]
# Support teacherni guruhga biriktirish
SUPPORT_ASSIGN = [FOUNDER, HEAD_SUPPORT, ACADEMIC_HEAD, HR_MANAGER]
# Ketma-ket nechta darsga kelmasa avtomat muzlatiladi
AUTO_FREEZE_ABSENCES = 3
# Junior teacher bo'lish shartlari (support teacher yo'li)
JUNIOR_PATH = [
    ("cert", "Sertifikat: CEFR B2 (kamida 55%)", 55.0),
    ("skill", "Dars berish mahorati balli (kamida 75)", 75.0),
    ("months", "Support/volontyor tajriba (kamida 3 oy)", 3.0),
]


# To'lov summasini tahrirlash — faqat asoschi, moliyachi va filial
# rahbari. Pul hujjatiga tegish huquqi tor doirada bo'ladi, har bir
# o'zgarish auditga yoziladi.
PAYMENT_EDIT = [FOUNDER, FINANCE_DIRECTOR, BRANCH_MANAGER]

# TO'LOVNI TUZATISH SO'ROVI (2026-08-15, Jahongir: "sotuv manager
# tolovni notogri urvordi ... sorov yuborsa filial rahbari yoki
# moliyachiga borsa yoki asoschiga tasdiqlavorsa ozgarsin").
#   - so'rovni KIM yubora oladi: kassaga tegadigan hamma xodim;
#   - kim TASDIQLAY oladi: tahrirlash huquqi borlar (o'zgarishni
#     ular baribir qo'lda ham qila olardi).
PAYMENT_FIX_REQUEST = list(dict.fromkeys(CASH_ACCESS + PAYMENT_EDIT))
PAYMENT_FIX_APPROVE = list(PAYMENT_EDIT)

PAYMENT_FIX_KINDS = [
    ("amount", "Summani to'g'rilash"),
    ("method", "To'lov usulini to'g'rilash"),
    ("note", "Izohni to'g'rilash"),
    ("delete", "Yozuvni bekor qilish"),
]
PAYMENT_FIX_KIND_LABELS = dict(PAYMENT_FIX_KINDS)

# ---------------------------------------------------------------------------
#  XAVFSIZLIK SIYOSATI
# ---------------------------------------------------------------------------
# Parol: kamida 8 belgi, ichida harf ham, raqam ham bo'lsin.
PASSWORD_MIN = 8
PASSWORD_RULE_TEXT = ("Parol kamida 8 belgi bo'lib, ichida harf ham, "
                      "raqam ham bo'lishi kerak")


# O'quvchi hisobi avtomat ochilganda beriladigan parol (2026-08-10).
# Login sahifasida shu parol bilan kirgan odamga "parolni
# o'zgartiring" deb eslatma chiqadi (Login.tsx).
DEFAULT_PASSWORD = "jonyjony"


def password_ok(pw: str) -> bool:
    pw = pw or ""
    return (len(pw) >= PASSWORD_MIN
            and any(c.isalpha() for c in pw)
            and any(c.isdigit() for c in pw))


# LOGIN (2026-09-16, Jahongir: "loginni ham har bir xodim va HR edit
# qila olsin"). Telefon raqam ham login bo'la oladi, shuning uchun
# faqat raqamdan iborat login ham to'g'ri.
USERNAME_MIN = 3
USERNAME_MAX = 40
USERNAME_RULE_TEXT = ("Login 3-40 belgi bo'lsin: lotin harflari, raqamlar "
                      "va . _ - @ belgilari, probelsiz")


def username_ok(name: str) -> bool:
    import re as _re
    return bool(_re.fullmatch(
        r"[A-Za-z0-9._@-]{%d,%d}" % (USERNAME_MIN, USERNAME_MAX),
        name or ""))


# Brute-force himoyasi: shu oynada shuncha xato — vaqtincha blok.
LOGIN_MAX_FAILS = 5
# Bitta IP dan (2026-09-06): bir markazdan bir nechta xodim kiradi,
# shuning uchun chegara kattaroq — lekin cheksiz emas.
LOGIN_MAX_FAILS_IP = 30
LOGIN_WINDOW_MIN = 15

# Ota-ona havolasi (login-siz, faqat token bilan): shuncha kundan
# keyin muddati tugaydi. Login talab qilinmagani uchun token
# muddatsiz yashasa, tasodifan (yoki Telegram guruhida, skrinshotda
# va h.k.) tarqalib qolgan eski havola abadiy ochiq qolardi.
# Muddati tugasa ham ma'lumot yo'qolmaydi - xodim "yangilash"
# tugmasi bilan bir zumda yangi havola chiqaradi.
PARENT_TOKEN_VALIDITY_DAYS = 180


def money(x) -> float:
    """Pul har doim butun so'mgacha yaxlitlanadi — Float ustunlarda
    kasr qoldig'i yig'ilib ketmasligi uchun yozishdan oldin shu
    yordamchidan o'tkaziladi."""
    return float(round(x or 0))


# =====================================================================
# TADBIRLAR VA TUG'ILGAN KUNLAR (2026-09-14)
#
# Jahongir: "event manager degan lavozim qoshib qoygin eventlarni
# tashkil qilish tugilgan kunlar avtomat korinib turishi kerak".
# Tug'ilgan kunlar qo'lda kiritilmaydi — o'quvchi va xodim kartasidagi
# birth_date dan har safar yangidan hisoblanadi.
# =====================================================================
EVENTS_ACCESS = FULL_ACCESS + [EVENT_MANAGER, HR_MANAGER, SMM_MANAGER]
EVENTS_MANAGE = FULL_ACCESS + [EVENT_MANAGER]
BIRTHDAY_HORIZON = 30            # standart: 30 kun oldindan ko'rsatiladi
# Qo'ng'iroqchada (bildirishnoma) necha kun oldindan chiqadi
# (2026-10-05): xodim sanalari STAFF_DATE_LEAD_DAYS bilan bir xil,
# o'quvchi tug'ilgan kuni va tadbirlar — 3 kun.
ALERT_BIRTHDAY_DAYS = 3
ALERT_EVENT_DAYS = 3
ALERT_CELEBRATION_MAX = 12       # bundan ko'pi "...va yana N ta" bo'ladi
EVENT_KINDS = [
    ("holiday", "Bayram"),
    ("birthday", "Tug'ilgan kun tabrigi"),
    ("contest", "Tanlov / olimpiada"),
    ("trip", "Sayohat / ekskursiya"),
    ("party", "Kecha / bitiruv"),
    ("seminar", "Seminar / master-klass"),
    ("other", "Boshqa"),
]
EVENT_KIND_LABELS = dict(EVENT_KINDS)
EVENT_STATUSES = [
    ("planned", "Rejada", "slate"),
    ("preparing", "Tayyorlanmoqda", "sky"),
    ("done", "O'tkazildi", "emerald"),
    ("cancelled", "Bekor qilindi", "rose"),
]
EVENT_STATUS_LABELS = {k: lbl for k, lbl, _ in EVENT_STATUSES}


# =====================================================================
#  NA'MUNALI XODIM — INTIZOM BALLI (2026-09-16)
#
#  Jahongir yuborgan "Na'munali xodim.xlsx" jadvali tizimga ko'chirildi.
#  Har xodim yilni 100 ball bilan boshlaydi. Qoidabuzarlik yozilganda
#  ball ayiriladi; bir xil qoidabuzarlik SHU OYNING ICHIDA takrorlansa
#  jarima oshib boradi (1-marta, 2-marta ... 5-marta va undan keyin
#  hammasi 5-martaniki). Keyingi oy hisob yana 1-martadan boshlanadi,
#  lekin ayirilgan ball yil davomida yig'ilib boradi.
#
#  Excel bilan bir xil: ball oylikka TA'SIR QILMAYDI — bu intizom
#  ko'rsatkichi, pastga tushsa jazo jadvali ishlaydi.
# =====================================================================
CONDUCT_START_POINTS = 100

# (kalit, nomi, 1..5-marta ayiriladigan ball)
CONDUCT_KINDS = [
    ("late", "Kech kelish", (1, 2, 3, 4, 5)),
    ("conflict_cause", "Ziddiyat — sababchi", (4, 6, 8, 10, 20)),
    ("conflict_part", "Ziddiyat — qatnashchi", (2, 4, 6, 10, 20)),
    ("badge", "Beyjik taqmaslik", (1, 2, 3, 4, 5)),
    ("manual", "Manualga amal qilmaslik", (1, 1, 2, 3, 5)),
]
CONDUCT_STEPS = {k: steps for k, _, steps in CONDUCT_KINDS}
# Excel'dagi "xayfsan uchun" ustuni: ball qo'lda yoziladi. Manfiy son
# ball QAYTARADI (Excel'da -1 yozilgan qatorlar shunday ishlagan).
CONDUCT_REPRIMAND = "reprimand"
CONDUCT_REPRIMAND_MAX = 50
CONDUCT_KIND_LABELS = {k: lbl for k, lbl, _ in CONDUCT_KINDS}
CONDUCT_KIND_LABELS[CONDUCT_REPRIMAND] = "Xayfsan (qo'lda ball)"

# Bo'limlar: support va examinerlar alohida, qolgan hamma xodim birinchisida
CONDUCT_SECTIONS = [
    ("staff", "Na'munali xodim"),
    ("support", "Na'munali support"),
    ("examiner", "Na'munali examiner"),
]
CONDUCT_SECTION_LABELS = dict(CONDUCT_SECTIONS)
CONDUCT_SECTION_ROLES = {
    "support": [SUPPORT_TEACHER, HEAD_SUPPORT],
    "examiner": [EXAMINER, HEAD_EXAMINER],
}
# Asoschi ro'yxatga kirmaydi — u baholovchi, baholanuvchi emas
CONDUCT_EXCLUDED = [FOUNDER] + EXTERNAL_ROLES


def conduct_section(role) -> str | None:
    if not role or role in CONDUCT_EXCLUDED:
        return None
    for key, rs in CONDUCT_SECTION_ROLES.items():
        if role in rs:
            return key
    return "staff"


# Kim ko'radi va yozadi (2026-09-16, Jahongir):
#   - HR — hamma bo'limda, hammani ("faqat HR ko'rib o'zgartira olsin");
#   - examinerlar boshlig'i — faqat oddiy examinerlarni, support rahbari —
#     faqat oddiy supportlarni ("examiner boshlig'i examinerlarni, support
#     manager esa supportlarni jarima ball qo'shsin");
#   - rahbarlarning O'ZINI faqat HR baholaydi ("o'zlarini esa HR
#     baholasin"). Asoschi bu bo'limda yo'q.
CONDUCT_MANAGE_ALL = [HR_MANAGER]
CONDUCT_SECTION_MANAGERS = {
    "examiner": [HEAD_EXAMINER],
    "support": [HEAD_SUPPORT],
}
# Rahbar kimni baholaydi: bo'lim -> baholanadigan rollar
CONDUCT_HEAD_TARGETS = {
    "examiner": [EXAMINER],
    "support": [SUPPORT_TEACHER],
}
CONDUCT_VIEW = list(dict.fromkeys(
    CONDUCT_MANAGE_ALL
    + [r for rs in CONDUCT_SECTION_MANAGERS.values() for r in rs]))


def conduct_sections_for(role) -> list:
    if role in CONDUCT_MANAGE_ALL:
        return [k for k, _ in CONDUCT_SECTIONS]
    return [k for k, rs in CONDUCT_SECTION_MANAGERS.items() if role in rs]


def conduct_can_rate(role, target_role) -> bool:
    """role egasi target_role egasiga ball yoza/ko'ra oladimi."""
    sec = conduct_section(target_role)
    if not sec:
        return False
    if role in CONDUCT_MANAGE_ALL:
        return True
    return (role in CONDUCT_SECTION_MANAGERS.get(sec, [])
            and target_role in CONDUCT_HEAD_TARGETS.get(sec, []))


def conduct_points(kind, nth: int) -> float:
    """Oy ichidagi nechanchi qoidabuzarlik -> ayiriladigan ball."""
    steps = CONDUCT_STEPS.get(kind)
    if not steps:
        return 0.0
    n = min(max(int(nth or 1), 1), len(steps))
    return float(steps[n - 1])


# JAZO jadvali (Excel "Jazo" varag'i): qolgan ball shu chegaraga
# tushsa yoki undan pastga tushsa. Pastdan yuqoriga tekshiriladi.
# (chegara, daraja, ustoz uchun, boshqa xodimlar uchun)
CONDUCT_SANCTIONS = [
    (-50, "dismiss", "Xodim bilan xayrlashiladi",
     "Xodim bilan xayrlashiladi"),
    (0, "severe", "Darajasi 2 taga tushiriladi va xayfsan beriladi",
     "Xayfsan beriladi"),
    (30, "demote", "Darajasi 1 taga tushiriladi", "Xayfsan beriladi"),
    (50, "warning", "Ogohlantirish beriladi", "Ogohlantiriladi"),
]


def conduct_sanction(remaining: float, role) -> dict | None:
    teacher = role == TEACHER
    for limit, level, t_text, o_text in CONDUCT_SANCTIONS:
        if remaining <= limit:
            return {"level": level, "limit": limit,
                    "text": t_text if teacher else o_text}
    return None


# =====================================================================
#  HR: QORA RO'YXAT (2026-09-16, Jahongir: "o'quv markaz qora
#  ro'yxatini shakllantir hr bo'limi uchun, bu bo'limga tushgan
#  nomzodlar boshqa ishga olinmasin").
#
#  Odam telefon raqami (oxirgi 9 raqam) va ism-familiyasi bo'yicha
#  tanib olinadi. Qora ro'yxatdagi odamni hech bir yo'l bilan ishga
#  olib bo'lmaydi: nomzodni "ishga olindi"ga o'tkazish, taklif berish,
#  xodim hisobi ochish, ustozga akkaunt berish, bo'shatilgan xodimni
#  qaytarish — hammasi to'xtatiladi. Ro'yxatdan chiqarish ham sabab
#  bilan va tarixda qoladi.
# =====================================================================
BLACKLIST_CATEGORIES = [
    ("discipline", "Intizom buzilishi"),
    ("theft", "O'g'irlik / moddiy zarar"),
    ("fraud", "Aldov / soxta hujjat"),
    ("conflict", "Janjal / hurmatsizlik"),
    ("left_bad", "Yomon sharoitda ishdan ketgan"),
    ("other", "Boshqa"),
]
BLACKLIST_CATEGORY_LABELS = dict(BLACKLIST_CATEGORIES)
# Ko'radi: asoschi, HR va filial rahbari (u ham xodim oladi).
# Qo'shadi / chiqaradi: faqat asoschi va HR.
BLACKLIST_MANAGE = [FOUNDER, HR_MANAGER]
BLACKLIST_VIEW = [FOUNDER, HR_MANAGER, BRANCH_MANAGER]


def blacklist_phone_key(phone) -> str | None:
    """Telefonning oxirgi 9 raqami: +998 90 123-45-67 va 901234567 bir xil."""
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    return digits[-9:] if len(digits) >= 9 else None


def blacklist_name_key(name) -> str | None:
    """Ism-familiya kaliti: katta-kichik harf, apostrof turlari, bo'shliq
    va so'zlar tartibi farq qilmaydi ("Ali Valiyev" = "valiyev  ali")."""
    table = str.maketrans({c: "'" for c in "’‘ʻʼ`´"})
    words = str(name or "").translate(table).lower().split()
    return " ".join(sorted(words)) if len(words) >= 2 else None


def default_pay_period(d, kind: str = "salary") -> str:
    """Oylik QAYSI OY UCHUN — beruvchi tanlamasa (2026-10-03, Jahongir:
    "sentabr oyinikini oktabrda berilsa ham sentabrniki bo'lib
    yozilsin"). Oyning 1–15 kunlarida berilgan oylik — o'tgan oyniki;
    avans esa doim shu oyniki (oy ichida oldindan beriladi)."""
    if kind != "advance" and d.day <= 15:
        y, m = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
        return f"{y:04d}-{m:02d}"
    return f"{d.year:04d}-{d.month:02d}"


# =====================================================================
#  DIAGNOSTIKA: "BILMAYMAN" VA "JUDA TEZ" HIMOYASI (2026-10-22)
#
#  Jahongir: "diagnostik testda hech narsani bilmay taxminan bosib
#  tashlaydiganlarning darajasi baland chiqyapti ... savolni o'qimay
#  bosib tashlaydiganlarni to'g'ri bossa ham noto'g'ri ko'rsatishi
#  kerak".
#
#  Savolni SERVER bergan paytdan javob kelgan paytgacha vaqtni server
#  o'zi o'lchaydi. Shu minimumdan tez kelgan javob kalitga mos bo'lsa
#  ham XATO hisoblanadi va "juda tez" deb yoziladi. Minimum odam
#  o'qishi kerak bo'lgan matn hajmidan chiqadi (placement_guard.py).
#  Uchala test — ingliz (entry.py _PT_*), nemis va rus — shu sonlarni
#  ishlatadi.
# =====================================================================
#
# 2026-10-22 (ko'rib chiqishdan keyin) — SONLAR YUMSHATILDI. Avval
# 1200 + 15/belgi, kamida 2 s edi: 360 grammatika savolining 130 tasi
# aynan 2 s polida turardi. Server vaqti tarmoq va sahifa chizilishini
# ham o'z ichiga oladi, shuning uchun bilimdon o'quvchi oson savolni
# 1.5–2 s da bossa ham "juda tez" bo'lib, adaptiv zina uni A1 gacha
# tushirib yuborardi (simulyatsiyada C1 o'quvchi 8 dan 6 marta past
# chiqdi). Endi minimum faqat "o'qishning IMKONI yo'q" tezlikni ushlaydi:
#   * bitta savol: 700 + 7 ms/belgi (~140 belgi/s — ravon o'qishdan
#     ~5 baravar tez), 1.5..5 s. Grammatika savoli 5 ta variant bilan
#     31–149 belgi (mediana 65): 60–120 belgi -> 1.5 s, eng uzuni ~1.75 s.
#     Tasodifiy bosuvchi (0.3–1.2 s) baribir ushlanadi;
#   * matnli ekran (reading 1-javobi): yana 12 ms/matn belgisi (~1000
#     so'z/daqiqa — ko'z yugurtirib o'qishdan ham tez), 3..20 s:
#     A1 matnlari (~180–350 belgi) -> 3.2–3.9 s, C1 (~980) -> 12.6–14.4 s;
#   * listening: yozuvning kamida yarmi (javob yozuv o'rtasida ham
#     eshitilishi mumkin), 5.5–31 s yozuv -> 2.75–15.4 s;
#   * lug'at ekrani (3 ta ta'rif): yig'indi, bugun 4.5 s, 10 s gacha;
#   * nemis/rus: bitta savol qoidasi, 1.5–3.9 s (mediana 1.5 s).
# Murosa (egasi hal qiladi): pol qancha past bo'lsa, bilimdon o'quvchi
# shuncha kam jazolanadi, lekin 1.5 s dan sekin "taxmin" qiluvchi ham
# ushlanmaydi. Adaptiv zinada tez-to'g'ri javob baribir pastga
# tushirmaydi (entry.py, "held").
PLACEMENT_MIN_BASE_MS = 700              # har savolga bazaviy vaqt
PLACEMENT_MIN_PER_CHAR_MS = 7            # savol + variantlar: 1 belgi uchun
PLACEMENT_MIN_SINGLE_FLOOR_MS = 1500     # bitta savol: eng kami
PLACEMENT_MIN_SINGLE_CEIL_MS = 5000      # bitta savol: eng ko'pi
PLACEMENT_MIN_PASSAGE_PER_CHAR_MS = 12   # matnli ekran: matnning 1 belgisi
PLACEMENT_MIN_PASSAGE_FLOOR_MS = 3000    # matnli ekrandagi 1-javob: eng kami
PLACEMENT_MIN_PASSAGE_CEIL_MS = 20000    # matnli ekrandagi 1-javob: eng ko'pi
PLACEMENT_MIN_CLIP_SHARE = 0.5           # listening: yozuvning kamida yarmi
PLACEMENT_MIN_SPEECH_WPS = 2.5           # yozuv uzunligi noma'lum: so'z/soniya
PLACEMENT_MIN_SCREEN_CEIL_MS = 10000     # lug'at ekrani birdan yuborilsa
# Minimum savol vaqtining 60 foizidan oshmaydi — aks holda uzun matnda
# odam ulgurmay qolishi mumkin edi (bugungi banklarda hech qayerda
# bunga yetmaydi, faqat ehtiyot chorasi).
PLACEMENT_MIN_LIMIT_SHARE = 0.6
PLACEMENT_GUESS_WARN_PCT = 30            # javoblarning >=30% juda tez bo'lsa
PLACEMENT_IDK_LABEL = "Bilmayman"
PLACEMENT_GUESS_LABEL = "Taxminan bosilgan bo'lishi mumkin"
# Nemis/rus testi: deploydan oldin ochilgan sahifa javoblarni eskicha
# (state'siz "answers") yuboradi — vaqt o'lchanmagan, "juda tez" qoidasi
# ishlamaydi. Bu yo'l faqat shu sanagacha (shu kun ham, UTC) ochiq:
# undan keyin 409 "Sahifani yangilang" — aks holda qo'lda yasalgan
# so'rov yoki yangilanmagan ofis/kiosk oynasi himoyani doim chetlab
# o'tardi. Deploy shu sanadan keyin bo'lsa — sanani surish kerak.
# Muddat ichida qabul qilingan bunday natija "o'lchanmagan" deb
# saqlanadi: timed=false, "juda tez" = None ("—", 0 emas) — xodim uni
# hech qachon "toza" natija deb o'qimaydi (placement_guard.untimed).
PLACEMENT_LEGACY_SUBMIT_UNTIL = "2026-10-29"
