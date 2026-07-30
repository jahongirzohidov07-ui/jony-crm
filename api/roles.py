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
