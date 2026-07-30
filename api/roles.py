"""Jony Academy tashkiliy rollari.

Muhim atama farqi: bizning o'quv markazda "Administrator" deganda
SOTUV MENEJERI tushuniladi (lidlar bilan ishlaydigan odam), tizimning
egasi emas. Tizimning to'liq huquqli egasi - ASOSCHI.

Ichki kalitlar (masalan "founder") bazada saqlanadi va hech qachon
o'zgarmasligi kerak; ekranda ko'rinadigan nom UZ_LABELS'da turadi.
"""

FOUNDER = "founder"                     # Asoschi - to'liq huquq
BRANCH_MANAGER = "branch_manager"       # Filial menejeri
SALES_MANAGER = "sales_manager"         # Administrator (sotuv menejeri)
TEACHER = "teacher"                     # O'qituvchi
SUPPORT_TEACHER = "support_teacher"
EXAMINER = "examiner"
HR_MANAGER = "hr_manager"
SMM_MANAGER = "smm_manager"
ACADEMIC_HEAD = "academic_head"         # O'quv bo'limi rahbari

ALL_ROLES = [
    FOUNDER,
    BRANCH_MANAGER,
    SALES_MANAGER,
    TEACHER,
    SUPPORT_TEACHER,
    EXAMINER,
    HR_MANAGER,
    SMM_MANAGER,
    ACADEMIC_HEAD,
]

UZ_LABELS = {
    FOUNDER: "Asoschi",
    BRANCH_MANAGER: "Filial menejeri",
    SALES_MANAGER: "Administrator (sotuv menejeri)",
    TEACHER: "O'qituvchi",
    SUPPORT_TEACHER: "Support teacher",
    EXAMINER: "Examiner",
    HR_MANAGER: "HR manager",
    SMM_MANAGER: "SMM manager",
    ACADEMIC_HEAD: "O'quv bo'limi rahbari",
}

# ---- Ruxsat guruhlari -------------------------------------------------
# Kundalik operatsion to'liq huquq (talaba/guruh yaratish-o'chirish,
# moliyaviy amallar). Asoschi + filial menejeri.
FULL_ACCESS = [FOUNDER, BRANCH_MANAGER]

# Talaba yozuvlari bilan ishlaydiganlar. Sotuv menejeri ham kiradi -
# lidni o'quvchiga aylantirish uning ishi.
TEACHING_STAFF = FULL_ACCESS + [SALES_MANAGER, TEACHER, SUPPORT_TEACHER,
                                EXAMINER, ACADEMIC_HEAD]

# Xodimlar ro'yxatini KO'RA oladiganlar.
STAFF_VIEWERS = FULL_ACCESS + [HR_MANAGER]

# Xodim yaratish va ROL BERISH - faqat asoschi. Bu ataylab eng tor
# guruh: rol berish tizimdagi eng xavfli amal.
USER_ADMIN = [FOUNDER]

# Moliya (to'lov, hisob-kitob, ish haqi).
FINANCE_ACCESS = FULL_ACCESS

# Lidlar (sotuv voronkasi). Administrator/sotuv menejeri bu yerda
# asosiy foydalanuvchi; SMM manager Instagram/Telegram lidlarini
# kiritadi; support teacher qabulda tashrifchilarni yozadi.
LEAD_ACCESS = FULL_ACCESS + [SALES_MANAGER, SMM_MANAGER, SUPPORT_TEACHER]

# Faqat umumiy statistikani ko'radiganlar.
DASHBOARD_ONLY = [SMM_MANAGER]

# Butun tashkilot bo'yicha ko'radigan rollar (filialga bog'lanmagan).
ORG_WIDE_ROLES = [FOUNDER, HR_MANAGER, SMM_MANAGER, ACADEMIC_HEAD]

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
AUDIT_VIEW = [FOUNDER, BRANCH_MANAGER]

# ---- Nozik ma'lumotlar ------------------------------------------------
# Support teacher va o'qituvchi to'lov tafsilotlarini ko'rmaydi:
# ularga o'quvchi qarzdor yoki yo'qligi yetarli, summa emas.
PAYMENT_DETAIL_VIEW = FULL_ACCESS + [SALES_MANAGER]

# Boshqa xodimning oyligini ko'rish - faqat asoschi va HR.
# O'qituvchi faqat O'ZINING oyligini ko'radi.
SALARY_VIEW_ALL = [FOUNDER, HR_MANAGER]

# Umumiy kompaniya foydasi - faqat asoschi va filial rahbari
# (rahbar o'z filiali bo'yicha). Sotuv menejeri ko'rmaydi.
PROFIT_VIEW = FULL_ACCESS

# Akademik baho qo'yish - faqat o'qituvchilar tarkibi.
# Kassir/sotuv menejeri bahoga tegmaydi.
GRADE_EDIT = FULL_ACCESS + [TEACHER, SUPPORT_TEACHER, EXAMINER, ACADEMIC_HEAD]

# ---- O'quv bo'limi ----------------------------------------------------
# Ta'lim sifatiga javob beradigan bo'lim: akademik risk, guruh to'lishi,
# xonalar. O'quv bo'limi rahbari butun markaz bo'yicha ko'radi.
ACADEMIC_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD]

# ---- Examiner (imtihon nazorati) --------------------------------------
# DIQQAT: Examiner o'quv bo'limiga EMAS, to'g'ridan-to'g'ri asoschiga
# bo'ysunadi. Shuning uchun imtihon moduli Audit bo'limida turadi -
# ta'lim sifatini o'lchayotgan odam o'lchanayotgan bo'limga qaram
# bo'lmasligi kerak.
EXAM_ACCESS = [FOUNDER, EXAMINER]
# Natijani KO'RA oladiganlar (kiritish EXAM_ACCESS'da).
EXAM_VIEW = EXAM_ACCESS + [BRANCH_MANAGER, ACADEMIC_HEAD, TEACHER]

# Testni TASDIQLASH - faqat examiner va asoschi.
EXAM_APPROVE = EXAM_ACCESS

# ---- Support teacher --------------------------------------------------
SUPPORT_ACCESS = FULL_ACCESS + [ACADEMIC_HEAD, SUPPORT_TEACHER]

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
ACADEMIC_VIEW = ACADEMIC_ACCESS + [TEACHER, SUPPORT_TEACHER, SALES_MANAGER]

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
MARKETING_ACCESS = FULL_ACCESS + [SMM_MANAGER]
MARKETING_CHANNELS = LEAD_SOURCES
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
TEACHING_ACCESS = FULL_ACCESS + [TEACHER, SUPPORT_TEACHER, EXAMINER,
                                 SALES_MANAGER, ACADEMIC_HEAD]
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
KPI_VIEW = FULL_ACCESS
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
