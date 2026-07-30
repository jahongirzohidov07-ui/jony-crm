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
FACILITY_MANAGER = "facility_manager"   # Xo'jalik ishlari menejeri

# ---- Tashqi foydalanuvchilar -----------------------------------------
PARENT = "parent"                       # Ota-ona
STUDENT = "student"                     # O'quvchi

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
    PARENT,
    STUDENT,
]

UZ_LABELS = {
    FOUNDER: "Asoschi",
    FINANCE_DIRECTOR: "Moliya direktori",
    ACCOUNTANT: "Buxgalter",
    BRANCH_MANAGER: "Filial rahbari",
    SALES_HEAD: "Sotuv rahbari",
    SALES_MANAGER: "Sotuv menejeri",
    ADMINISTRATOR: "Administrator",
    SMM_MANAGER: "Marketolog / SMM",
    ACADEMIC_HEAD: "O'quv bo'limi rahbari",
    TEACHER: "O'qituvchi",
    SUPPORT_TEACHER: "Support teacher",
    HEAD_SUPPORT: "Support teacherlar boshlig'i",
    EXAMINER: "Examiner",
    HEAD_EXAMINER: "Examinerlar boshlig'i",
    HR_MANAGER: "HR menejer",
    FACILITY_MANAGER: "Xo'jalik ishlari menejeri",
    PARENT: "Ota-ona",
    STUDENT: "O'quvchi",
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
    ("support", "Qo'llab-quvvatlash", [HR_MANAGER, FACILITY_MANAGER]),
    ("external", "Tashqi", [PARENT, STUDENT]),
]

# Tashqi foydalanuvchilar - ular xodim emas, ish haqi ham yo'q,
# xodimlar ro'yxatida ham chiqmaydi.
EXTERNAL_ROLES = [PARENT, STUDENT]
STAFF_ROLES = [r for r in ALL_ROLES if r not in EXTERNAL_ROLES]

# ---- Ruxsat guruhlari -------------------------------------------------
# Bular STANDART holat. Asoschi ruxsatlar matritsasidan o'zgartirsa,
# baza jadvalidagi qiymat ustun turadi.

# Kundalik operatsion to'liq huquq.
FULL_ACCESS = [FOUNDER, BRANCH_MANAGER]

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
ORG_WIDE_ROLES = [
    FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, HR_MANAGER, SMM_MANAGER,
    ACADEMIC_HEAD, SALES_HEAD, HEAD_EXAMINER, HEAD_SUPPORT,
    FACILITY_MANAGER,
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

    ("admin_salary", "Ma'muriy xodim oyligi", "admin_salary"),
    ("support_salary", "Farrosh / qorovul", "admin_salary"),
    # Eski "salary" kaliti ham ma'muriy xodimlarni bildirgan.
    ("salary", "Xodimlar oyligi (eski)", "admin_salary"),

    ("ads", "Reklama", "marketing"),
    ("tax", "Soliq", "tax"),
    ("repair", "Ta'mir", "other"),
    ("other", "Boshqa", "other"),
]

EXPENSE_CATEGORIES = [c for c, _, _ in EXPENSE_CATEGORY_DEFS]
EXPENSE_CATEGORY_LABELS = {c: lbl for c, lbl, _ in EXPENSE_CATEGORY_DEFS}
EXPENSE_CATEGORY_GROUP = {c: g for c, _, g in EXPENSE_CATEGORY_DEFS}

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
    "referral",   # Tanish orqali
    "ads",        # Reklama
    "other",      # Boshqa
]

# Manba lidni voronkaning qaysi nuqtasiga qo'yishini belgilaydi.
LEAD_SOURCE_DEFAULT_STAGE = {
    "visit": "trial_scheduled",
    "phone": "contacted",
    "instagram": "new",
    "telegram": "new",
    "referral": "new",
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
    "referral": "Tanish orqali",
    "ads": "Reklama",
    "other": "Boshqa",
}
MARKETING_CHANNEL_LABELS = {
    "visit": "Tashrif",
    "phone": "Telefon",
    "instagram": "Instagram",
    "telegram": "Telegram",
    "referral": "Tanish orqali",
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
}

# Kunlik baho shkalasi: ustoz har dars uchun 1-5 qo'yadi va o'sha ball
# aynan shuncha coinga teng (foydalanuvchi qoidasi).
DAILY_GRADE_MIN = 1
DAILY_GRADE_MAX = 5

# Imtihon natijasidan coin: foiz shu qiymatdan katta yoki teng bo'lsa,
# eng yuqori mos qator ishlaydi. Bu faqat BOSHLANG'ICH jadval - asoschi
# uni Gamification bo'limidan o'zgartira oladi.
DEFAULT_EXAM_COIN_RULES = [
    (90.0, 50),
    (80.0, 30),
    (70.0, 15),
    (60.0, 5),
]

# ---- Ruxsatlar --------------------------------------------------------
# Davomat va imtihon jadvalini ko'rish/yuritish. Administrator (sotuv
# menejeri) ham kiradi: yoqlama hisob-kitobga ta'sir qiladi va uni
# ko'pincha qabuldagi administrator qo'yadi.
# DIQQAT: akademik BAHO bunga kirmaydi - u alohida GRADE_EDIT bilan
# himoyalangan (yuqoriga qarang).
TEACHING_ACCESS = FULL_ACCESS + [
    TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT, EXAMINER, HEAD_EXAMINER,
    SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, ACADEMIC_HEAD,
]
# Sovg'a ro'yxati, coin qoidasi va qo'lda coin berish - faqat rahbariyat.
COIN_ADMIN = FULL_ACCESS

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

SUBJECTS = [
    ("english", "Ingliz tili"),
    ("russian", "Rus tili"),
    ("korean", "Koreys tili"),
    ("turkish", "Turk tili"),
    ("german", "Nemis tili"),
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

SUBJECT_LEVELS = {
    "english": ENGLISH_LEVELS,
    "russian": CEFR_LEVELS,
    "korean": CEFR_LEVELS,
    "turkish": CEFR_LEVELS,
    "german": CEFR_LEVELS,
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

# Darslar orasidagi mantiqsiz bo'shliq. Ustoz 09:00 da dars berib,
# keyingisi 19:00 da bo'lsa - kuni behuda ketadi.
MAX_GAP_HOURS = 5

CHECKS = [
    ("teacher_clash", "Ustoz bir vaqtda ikki guruhda", "block"),
    ("room_clash", "Xona bir vaqtda ikki guruhda", "block"),
    ("over_capacity", "Sig'imdan ortiq o'quvchi", "block"),
    ("teacher_overload", "Ustozning maksimal yuklamasidan oshish", "block"),
    ("bad_gap", "Darslar orasida mantiqsiz bo'shliq", "warn"),
    ("level_mismatch", "O'quvchi darajasiga mos bo'lmagan guruh", "warn"),
]
CHECK_LABELS = {k: lbl for k, lbl, _ in CHECKS}
CHECK_SEVERITY = {k: sev for k, _, sev in CHECKS}


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
]
DISCOUNT_TYPE_LABELS = {k: lbl for k, lbl, _ in DISCOUNT_TYPES}
DISCOUNT_TYPE_HINTS = {k: h for k, _, h in DISCOUNT_TYPES}

# Qaysi chegirmani tizim o'zi boshqaradi - qo'lda tegilmaydi.
AUTO_DISCOUNT_TYPES = ["family"]

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
    ("cancelled", "Bekor qilingan"),
    ("rejected", "Rad etilgan"),
]
DISCOUNT_STATUS_LABELS = dict(DISCOUNT_STATUSES)

# Bitta o'quvchida jami chegirma shundan oshmasin - aks holda o'qish
# tekinga aylanadi.
MAX_TOTAL_DISCOUNT_PERCENT = 50.0


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
    ("in", "Kirim"),
    ("out", "Chiqim"),
    ("write_off", "Hisobdan chiqarish"),
    ("correction", "Tuzatish"),
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

SALARY_PAY = FULL_ACCESS + [FINANCE_DIRECTOR, ACCOUNTANT]
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
    ("unknown", "Sababi noma'lum", "unknown"),
]
LEAVE_REASON_LABELS = {k: lbl for k, lbl, _ in LEAVE_REASONS}
LEAVE_REASON_GROUP = {k: g for k, _, g in LEAVE_REASONS}

# Bizga bog'liq sabablar - shularni kamaytirish mumkin
CONTROLLABLE_REASONS = ["teacher", "result", "competitor", "schedule"]


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
XP_LEAGUES = [
    (1, "newcomer", "Newcomer", 0, 99, "#f1f5f9", "🌱", 0),
    (2, "amateur", "Amateur", 100, 199, "#d4d4d8", "🔰", 1),
    (3, "wood", "Wood", 200, 399, "#a8a29e", "🪵", 2),
    (4, "stone", "Stone", 400, 599, "#78716c", "🪨", 4),
    (5, "bronze", "Bronze", 600, 999, "#d97706", "🥉", 6),
    (6, "silver", "Silver", 1000, 1499, "#94a3b8", "🥈", 10),
    (7, "gold", "Gold", 1500, 1999, "#f59e0b", "🥇", 15),
    (8, "crystal", "Crystal", 2000, 2999, "#8b5cf6", "💎", 20),
    (9, "elite", "Elite", 3000, 4999, "#ef4444", "⚔️", 25),
    (10, "master", "Master", 5000, 7999, "#22c55e", "🎓", 30),
    (11, "titan", "Titan", 8000, 11999, "#0ea5e9", "🗿", 50),
    (12, "champion", "Champion", 12000, 19999, "#eab308", "🏆", 60),
    (13, "legendary", "Legendary", 20000, 49999, "#991b1b", "🔥", 80),
    (14, "goat", "G.O.A.T", 50000, None, "#0f172a", "🐐", 100),
]
LEAGUE_LABELS = {k: lbl for _r, k, lbl, _a, _b, _c, _i, _co in XP_LEAGUES}

# Level = floor(Lifetime XP / XP_PER_LEVEL) + 1
XP_PER_LEVEL = 100


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
]
PILLAR_LABELS = {k: lbl for k, lbl, _t, _d in CONTENT_PILLARS}
PILLAR_TONE = {k: t for k, _l, t, _d in CONTENT_PILLARS}

FUNNEL_STAGES = [
    ("tofu", "Tanishtirish (TOFU)"),
    ("mofu", "Qiziqtirish (MOFU)"),
    ("bofu", "Qaror (BOFU)"),
    ("retention", "Saqlab qolish"),
]
FUNNEL_LABELS = dict(FUNNEL_STAGES)

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
    ("reach", "Reach"),
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
